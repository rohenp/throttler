import threading
import time

def throttle(current_func, period=5000):
    """
    Generate a function that executes only once within the given period. If the function is unable to execute,
    it will delay and execute when possible to avoid dropping a function call. This is feature is limited
    by the size of the thread pool, managed by `THREAD_POOL_SIZE`.

    :param current_func: function to execute if not throttled
    :param period: period in milliseconds
    return: throttled function wrapper
    """

    THREAD_POOL_SIZE = 50
    thread_pool = []

    # Use a list to keep track of the relevant variables, as the list will maintain scope
    exec_list = [
        None,
        threading.Lock()
    ]

    def throttled_function():
        """
        Throttled function that executes the orignal function. The call is wrapped in a threaded function,
        allowing the thread to continue to execute the function later if it is being throttled.

        return: return value of the throttled function
        """

        def threaded_call():
            """
            This function operates inside of a thread, continually trying to execute with a related sleep pattern
            to complete its operation. It attempts to acquire a lock on a variable to update it. If it cannot, it
            keeps attempting to get a lock. If a lock is obtained and the valid cases are found, the function
            executes.

            return: return value of the throttled function
            """

            return_value = None

            # The thread should loop until it finally meets its exit conditions
            while True:
                # Unpack the lock
                lock = exec_list[1]
                
                # If an attempt on a non-blocking lock fails, loop. The lock needs to be acquired before evaluating
                # logic conditions as the logic conditions may change due to another thread if there is no lock.
                if not lock.acquire(False):
                    continue

                # Unpack the variables
                last_execution_time = exec_list[0]

                # Determine the current time. Performing this at once at the top will help remove any race conditions
                # that may impace the sleep call in the else case
                now = time.time()
                period_in_seconds = period / 1000.0

                # Period needs to be converted from milliseconds to seconds in this case. A float is used to avoid
                # losing precision if a small millisecond value is used
                if last_execution_time is None or now - last_execution_time >= period_in_seconds:
                    
                    # Call the function carefully
                    try: 
                        return_value = current_func()
                    finally:
                        # Update the item in the list. Lock has been acquired, so it's safe
                        exec_list[0] = time.time()
                    
                        # Release the lock
                        lock.release()

                        # Break the loop
                        break
                else:
                    # Release the lock
                    lock.release()
                    
                    # Sleep the difference of the required period and how much time has actually elapsed
                    # Period is greater than the elapsed time between the current attempt and the period call
                    # If this function is expected to hit very high load, another solution would be to use
                    # a backoff algorithm to deal with retries in more staggered way
                    time.sleep(period_in_seconds - (now - last_execution_time))

            # The throttle case has been cleared, so it is safe to execute the function at this point
            return return_value

        # Get a lock when checking the thread pool size and changing the thread pool
        # This may hit the scheduler pretty hard when trying to acquire a lock here. A delay may be
        # appropriate in such a case where the function is under considerable parallel load
        lock = exec_list[1]
        lock.acquire()

        # Clean the thread pool by removing dead threads
        stopped_threads = [thread for thread in thread_pool if not thread.is_alive()]
        for thread in stopped_threads:
            thread_pool.remove(thread)

        # Limit the size of the thread pool for sanity. Make sure to release the lock after the operations
        try:
            if len(thread_pool) == THREAD_POOL_SIZE:
                raise Exception("Thread pool is full. No more threads can be added.")

            # Build the thread, but don't start it yet
            t = threading.Thread(target=threaded_call)

            # Add the thread to the pool so we can track it
            thread_pool.append(t)
        finally:
            lock.release()

        # Start the thread
        t.start()

    return throttled_function

# Test code

def print_test():
    print('Executing function')

if __name__ == "__main__":
    throttled_function = throttle(print_test, 500)

    for _ in range(15):
        t = threading.Thread(target=throttled_function)
        t.start()
