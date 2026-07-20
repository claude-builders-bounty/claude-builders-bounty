#!/usr/bin/env python3
import sys
def main():
    pr = sys.argv[1] if len(sys.argv)>1 else ""
    print(f"Review placeholder for PR: {pr}")
if __name__=="__main__":
    main()
