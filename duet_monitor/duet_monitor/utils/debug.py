import sys

DEBUG = True

def debug_print_main(*args, **kwargs):
    if DEBUG:
        message = " ".join(str(arg) for arg in args)
        print("[메인 모듈 디버그]", message, **kwargs)
        sys.stdout.flush() 