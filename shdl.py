#!/usr/bin/env python3

# trigger

if __name__ == '__main__':
    try:
        from shdl import main

        main()
    except KeyboardInterrupt:
        # do nothing
        pass
