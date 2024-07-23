package main

import (
	"bufio"
	"bytes"
	"log"
	"os"
	"os/exec"
	"runtime"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
)

const inputFilePath = "check/testset/compbnd_large.test"
const outputFilePath = "check/testset/compbnd_filtered.test"
const gcgCommand = "./bin/gcg"

const parameters = "set limits time 60"

var totalPaths int32
var acceptedPaths int32
var processedPaths int32
var failedPaths []string
var failedPathsMutex sync.Mutex

func main() {
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
	results := make(chan string, len(paths))
	semaphore := make(chan struct{}, runtime.NumCPU()-2)

	for i, p := range paths {
		wg.Add(1)
		go func(p string, index int) {
			defer wg.Done()
			semaphore <- struct{}{}
			defer func() { <-semaphore }()
			if checkPath(p) {
				results <- p
				atomic.AddInt32(&acceptedPaths, 1)
			}
			processed := atomic.AddInt32(&processedPaths, 1)
			accepted := atomic.LoadInt32(&acceptedPaths)
			log.Printf("Processed %d/%d (%.2f%%), Accepted: %d/%d (%.2f%%), Path: %s",
				processed, totalPaths, float64(processed)/float64(totalPaths)*100,
				accepted, totalPaths, float64(accepted)/float64(totalPaths)*100, p)
		}(p, i)
	}

	wg.Wait()
	close(results)

	outputFile, err := os.Create(outputFilePath)
	if err != nil {
		log.Fatalf("Failed to create output file: %v", err)
	}
	defer outputFile.Close()

	for result := range results {
		_, err := outputFile.WriteString(result + "\n")
		if err != nil {
			log.Fatalf("Failed to write to output file: %v", err)
		}
	}

	// Process failed paths sequentially
	if len(failedPaths) > 0 {
		log.Printf("Retrying failed paths: %d paths", len(failedPaths))
		for _, p := range failedPaths {
			if checkPathSequential(p) {
				_, err := outputFile.WriteString(p + "\n")
				if err != nil {
					log.Fatalf("Failed to write to output file: %v", err)
				}
				atomic.AddInt32(&acceptedPaths, 1)
			}
			processed := atomic.AddInt32(&processedPaths, 1)
			accepted := atomic.LoadInt32(&acceptedPaths)
			log.Printf("Retry Processed %d/%d (%.2f%%), Accepted: %d/%d (%.2f%%), Path: %s",
				processed, totalPaths, float64(processed)/float64(totalPaths)*100,
				accepted, totalPaths, float64(accepted)/float64(totalPaths)*100, p)
		}
	}

	log.Printf("Accepted %d/%d (%.2f%%) paths", acceptedPaths, totalPaths, float64(acceptedPaths)/float64(totalPaths)*100)
}

func checkSuccessfulRun(p string, out bytes.Buffer) bool {
	scanner := bufio.NewScanner(&out)
	lines := make([]string, 0)
	for scanner.Scan() {
		line := scanner.Text()
		lines = append(lines, line)
		if strings.HasPrefix(line, "  generic") {
			parts := strings.Fields(line)
			if len(parts) > 1 {
				lastNumber := parts[len(parts)-1]
				i, err := strconv.Atoi(lastNumber)
				if err != nil {
					panic(err)
				}
				if i > 1 {
					return true
				} else {
					log.Printf("Path %s has only %d nodes", p, i)
					return false
				}
			}
		}
	}

	if err := scanner.Err(); err != nil {
		log.Printf("Error reading output for path %s: %v", p, err)
	}

	return false
}

func buildCommand(p string) *exec.Cmd {
	split := strings.Split(p, ";")
	instance := split[0]
	if len(split) > 1 {
		decomposition := split[1]
		return exec.Command(gcgCommand, "-c", parameters+" r check/"+instance+" r check/"+decomposition+" opt checksol disp stat q")
	} else {
		return exec.Command(gcgCommand, "-c", parameters+" r check/"+instance+" opt checksol disp stat q")
	}
}

func checkPath(p string) bool {
	cmd := buildCommand(p)
	log.Printf("Command: %s", cmd.String())
	var out bytes.Buffer
	cmd.Stdout = &out

	if err := cmd.Run(); err != nil {
		log.Printf("Failed to execute command for path %s: %v", p, err)
		log.Printf("\tFailed command: %s", cmd.String())
		failedPathsMutex.Lock()
		failedPaths = append(failedPaths, p)
		failedPathsMutex.Unlock()
		return false
	}

	return checkSuccessfulRun(p, out)
}

func checkPathSequential(p string) bool {
	log.Printf("Retrying path: %s", p)
	cmd := buildCommand(p)
	var out bytes.Buffer
	cmd.Stdout = &out

	if err := cmd.Run(); err != nil {
		log.Printf("Failed again to execute command for path %s: %v", p, err)
		log.Printf("\tFailed command: %s", cmd.String())
		return false
	}

	return checkSuccessfulRun(p, out)
}
