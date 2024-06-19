package main

import (
	"bufio"
	"bytes"
	"fmt"
	"io"
	"log"
	"os"
	"os/exec"
	"strings"
	"sync"
	"sync/atomic"
)

const (
	inputFilePath             = "check/testset/compbnd_filtered.test"
	settingsFile              = "validate.set"
	masterSettingsFileGeneric = "mastersettings_file_generic"
	masterSettingsFileCompbnd = "mastersettings_file_compbnd"
	logFilePath               = "validate.log"
)

var (
	totalPaths      int32
	processedPaths  int32
	failedPaths     []string
	failedMutex     sync.Mutex
	succeededChecks int32
	failedChecks    int32
)

func main() {
	// Setup logging to file and console
	logFile, err := os.OpenFile(logFilePath, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0666)
	if err != nil {
		log.Fatalf("Failed to open log file: %v", err)
	}
	defer logFile.Close()
	log.SetOutput(logFile)
	mw := io.MultiWriter(os.Stdout, logFile)
	log.SetOutput(mw)

	// Read paths from input file
	file, err := os.Open(inputFilePath)
	if err != nil {
		log.Fatalf("Failed to open input file: %v", err)
	}
	defer file.Close()

	var paths []string
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := scanner.Text()
		if line != "" {
			paths = append(paths, line)
		}
	}

	if err := scanner.Err(); err != nil {
		log.Fatalf("Failed to read input file: %v", err)
	}

	totalPaths = int32(len(paths))
	var wg sync.WaitGroup
	semaphore := make(chan struct{}, 16)

	for i, p := range paths {
		wg.Add(1)
		go func(p string, index int) {
			defer wg.Done()
			semaphore <- struct{}{}
			defer func() { <-semaphore }()
			if !processPath(p) {
				failedMutex.Lock()
				failedPaths = append(failedPaths, p)
				failedMutex.Unlock()
			}
			processed := atomic.AddInt32(&processedPaths, 1)
			success := atomic.LoadInt32(&succeededChecks)
			failed := atomic.LoadInt32(&failedChecks)
			log.Printf("Processed %d/%d (%.2f%%), Succeeded: %d, Failed: %d, Path: %s", processed, totalPaths, float64(processed)/float64(totalPaths)*100, success, failed, p)
		}(p, i)
	}

	wg.Wait()
	log.Println("Parallel processing completed. Retrying failed paths sequentially...")
	for _, p := range failedPaths {
		if !processPath(p) {
			log.Printf("Sequential retry failed for path: %s", p)
		}
	}
	log.Println("Processing completed.")
}

func processPath(p string) bool {
	log.Printf("Processing path: %s", p)
	output1, err1 := runCommand(p, masterSettingsFileGeneric)
	if err1 != nil {
		log.Printf("Run1 failed for path %s: %v", p, err1)
		atomic.AddInt32(&failedChecks, 1)
		return false
	}
	output2, err2 := runCommand(p, masterSettingsFileCompbnd)
	if err2 != nil {
		log.Printf("Run2 failed for path %s: %v", p, err2)
		atomic.AddInt32(&failedChecks, 1)
		return false
	}
	if compareOutputs(output1, output2) {
		log.Printf("Path %s passed comparison.", p)
		atomic.AddInt32(&succeededChecks, 1)
		return true
	}
	log.Printf("Path %s failed comparison: Primal bounds did not match or solution not feasible.", p)
	atomic.AddInt32(&failedChecks, 1)
	return false
}

func runCommand(p, masterSettingsFile string) (string, error) {
	cmd := exec.Command("./bin/gcg", "-s", settingsFile, "-m", masterSettingsFile, "-c", fmt.Sprintf("r check/%s opt checksol q", p))
	var out bytes.Buffer
	cmd.Stdout = &out
	cmd.Stderr = &out
	err := cmd.Run()
	return out.String(), err
}

func compareOutputs(output1, output2 string) bool {
	status1, primalBound1 := extractValues(output1)
	status2, primalBound2 := extractValues(output2)

	if !strings.Contains(status1, "solution is feasible in original problem") {
		log.Printf("Validation failed for Run1: solution is not feasible in original problem")
		return false
	}
	if !strings.Contains(status2, "solution is feasible in original problem") {
		log.Printf("Validation failed for Run2: solution is not feasible in original problem")
		return false
	}

	diff := primalBound1 - primalBound2
	if diff < 0 {
		diff = -diff
	}
	if diff > 0.0001 {
		log.Printf("Validation failed: Primal bounds differ more than 0.0001 (Run1: %f, Run2: %f)", primalBound1, primalBound2)
		return false
	}
	return true
}

func extractValues(output string) (status string, primalBound float64) {
	lines := strings.Split(output, "\n")
	for _, line := range lines {
		if strings.Contains(line, "solution is feasible in original problem") {
			status = line
		}
		if strings.HasPrefix(line, "Primal Bound") {
			parts := strings.Fields(line)
			fmt.Sscanf(parts[3], "%f", &primalBound)
		}
	}
	return status, primalBound
}
