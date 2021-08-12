import sys
import select

def run():
    poll = select.poll()
    poll.register( sys.stdin, select.POLLIN )
    
    while True:    
        res = poll.poll()        
        ch = res[0][0].read(1)
        print("Got " + ch)

run()
