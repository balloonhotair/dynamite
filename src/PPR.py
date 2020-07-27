import multiprocessing.pool
import collections
import threading
import importlib
import traceback
import time
import os
 
def run_functions(params):
    ((instance, func), args) = params
    try:
        return (getattr(instance(), func)(*args) if func != None else instance(*args))
    except KeyboardInterrupt:
        os._exit(1);
    except Exception:
        print(traceback.format_exc())

class PPR:
    functions, args = [], []
    
    def __init__(self, instance_name, processes = None):
        if instance_name != None:
            self.cpu_count = multiprocessing.cpu_count() if processes == None else processes
            try:
                self.pool = multiprocessing.Pool(processes)
                try:os.remove("stop_PPR_stop")
                except:pass
            except:
                self.pool = multiprocessing.pool.ThreadPool(processes)
            thread = threading.Thread(target=self.terminate_pool, args=())
            thread.daemon = True
            thread.start() 
            if isinstance(instance_name, str):
                self.instance = (getattr(importlib.import_module(instance_name), instance_name), False)
            elif isinstance(instance_name, tuple):
                self.instance = (getattr(instance_name[0], instance_name[1]), False) if instance_name[1] != None else (instance_name[0], True)
            else:
                print("Invalid Instance Name")          
         
    def create_processes(self, function = None, args = None, size = None, callback = None, async = False, queue = False):
        def get_func(func):
            return (getattr(self.instance[0], func), None) if self.instance[1] else (self.instance[0], func)
        
        if function == None:
            return self.create_processes(self.functions, self.args, size, callback, async)
        if queue:
            self.functions.append(function)
            self.args.append(args)
            return
        if size != None and size != 0:
            rslt = getattr(self.pool,"apply_async" if async else "map")(run_functions,[(get_func(function), t) for t in self.process_begin_size_tuple(args, (0, size))],)
        else:
            if isinstance(args, list):
                processes, rslt = [], []
                for i in range(len(args)):
                    processes.append(self.pool.apply_async(run_functions, [(get_func(function[i] if isinstance(function, list) else function), args[i]),]))
                for r in range(len(processes)): (rslt.append({r: processes[r]}) if async else rslt.append(processes[r].get()))
            else:
                rslt = getattr(self.pool,"apply_async" if async else "map")(run_functions, [(get_func(function), args)])
        if size != None and not async and abs(size) != len(rslt):
            raise TypeError("Length of Expected Results does not equal Return Results  %s %s" % len(rslt), abs(size))
        if async or rslt == None or len(rslt) == 0: return {} if callback == None else callback({})
        if not any(rslt): return rslt
        results = collections.OrderedDict((key,d[key]) for d in sorted(rslt, key = lambda d: list(d.keys())[0]) for key in d)
        return results if callback == None else callback(results)
    
    def terminate_pool(self):
        while not os.path.exists('stop_PPR_stop'):time.sleep(1)
        self.pool.close()
        self.pool.terminate()
        os._exit(0)
            
    def process_begin_size_tuple(self, arg, params):
        (begin, size) = params
        args = []
        start = begin
        end = size
        if size < 0:
            for s in range(size*-1):
                args.append((arg + (s,)))
        elif (size > self.cpu_count):
            for cpu in range(self.cpu_count):
                if (cpu == 0):
                    start = begin
                    end = (int)(size/self.cpu_count) + begin
                elif (cpu == self.cpu_count -1): 
                    start = ((int)(size/self.cpu_count) * cpu) + begin
                    end = size + begin
                else:
                    start = ((int)(size/self.cpu_count) * cpu) + begin
                    end = ((int)(size/self.cpu_count) * (cpu + 1)) + begin
                args.append((arg + (start,) + (end,)))
        else:
            args.append((arg + (start,) + (size,)))
        return args
        
if __name__ == '__main__':
    PPR(None)