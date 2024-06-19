package main

import (
	"bufio"
	"bytes"
	"log"
	"os"
	"os/exec"
	"strings"
	"sync"
	"sync/atomic"
)

const inputFilePath = "check/testset/compbnd_large.test"
const outputFilePath = "check/testset/compbnd_filtered.test"
const gcgCommand = "./bin/gcg"

const parameters = "set limits time 300" +
	" set limits nodes 2100000000" +
	" set lp advanced threads 1" +
	" set timing clocktype 1"

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
	semaphore := make(chan struct{}, 16)

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

func checkPath(p string) bool {
	cmd := exec.Command(gcgCommand, "-c", parameters+" r check/"+p+" opt disp stat q")
	var out bytes.Buffer
	cmd.Stdout = &out

	if err := cmd.Run(); err != nil {
		log.Printf("Failed to execute command for path %s: %v", p, err)
		failedPathsMutex.Lock()
		failedPaths = append(failedPaths, p)
		failedPathsMutex.Unlock()
		return false
	}

	scanner := bufio.NewScanner(&out)
	for scanner.Scan() {
		line := scanner.Text()
		if strings.HasPrefix(line, "  generic") {
			parts := strings.Fields(line)
			if len(parts) > 1 {
				lastNumber := parts[len(parts)-1]
				if lastNumber != "0" {
					return true
				}
			}
		}
	}

	if err := scanner.Err(); err != nil {
		log.Printf("Error reading output for path %s: %v", p, err)
	}

	return false
}

func checkPathSequential(p string) bool {
	log.Printf("Retrying path: %s", p)
	cmd := exec.Command(gcgCommand, "-c", parameters+" r check/"+p+" opt disp stat q")
	var out bytes.Buffer
	cmd.Stdout = &out

	if err := cmd.Run(); err != nil {
		log.Printf("Failed again to execute command for path %s: %v", p, err)
		return false
	}

	scanner := bufio.NewScanner(&out)
	for scanner.Scan() {
		line := scanner.Text()
		if strings.HasPrefix(line, "  generic") {
			parts := strings.Fields(line)
			if len(parts) > 1 {
				lastNumber := parts[len(parts)-1]
				if lastNumber != "0" {
					return true
				}
			}
		}
	}

	if err := scanner.Err(); err != nil {
		log.Printf("Error reading output for path %s: %v", p, err)
	}

	return false
}
