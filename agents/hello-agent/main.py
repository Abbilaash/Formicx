#!/usr/bin/env python3
import time

def main():
    print("Hello Agent started", flush=True)
    count = 0
    while True:
        count += 1
        print(f"Hello from Formicx #{count}", flush=True)
        time.sleep(0.5)

if __name__ == "__main__":
    main()
