import concurrent.futures
import logging

class TaskResult(object):
    """Store information about completed tasks"""

    def __init__(self, task, iter_id, taskresult=None, faildata=None, passdata=None):
        self.function = task
        self.function_name =self.function.__name__
        self.iter_id = iter_id
        self.task_complete = taskresult
        self.failure_data = faildata
        self.return_data = passdata


class TaskComplete(object):
    """Extend RunParallel with the results of the function execution"""

    def __init__(self, function=None, iterable=None, max_parallel=None, *opt_args, **opt_kwargs) -> None:
        pass


class RunParallel(object):
    """Store parameters and execute parallelized functions"""

    def __init__(self, function, iterable, *opt_args,  max_parallel=None, **opt_kwargs) -> None:
        """
        Create parallel execution options. 
        function should be the function to be parallelized
        iterable should be an iterable object (string, dict, obj, etc) where each element is the function's expected input
        max_parallel can be useful to avoid choking out resources.
        opt_args and opt_kwargs allow for non-iterating input to the parallelized function
       
        If max_parallel=None, default Python behavior is min(32, os.cpu_count() + 4)
        """

        self.function = function
        self.function_name = self.function.__name__
        self.iterable = iterable
        self.max_parallel = max_parallel
        self.opt_args = opt_args
        self.opt_kwargs = opt_kwargs

        # Store the completion status
        self.execution_started = False
        self.execution_complete = False
        self.passed_tasks = None
        self.failed_tasks = None

    def execute(self, fail_on_false=False):
        """Start the execution of the inputs. 
        If fail_on_false=True, any fct that returns False is marked as a failed_task"""

        # TODO: Complete fail_on_false logic
        
        successful_tasks = []
        failed_tasks = []
        logging.debug(f"RUN_PARALLEL: {self.iterable}")
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_parallel) as executor:
            
            # create a dict where each key is a scheduled thread with 1 thread per object and value is RsuConnection object
            logging.debug("THREAD STARTED")
            tasks_to_thread = {executor.submit(self.function, tgt_id, *self.opt_args, **self.opt_kwargs): 
                                tgt_id for tgt_id in self.iterable}
            self.execution_started = True
            logging.debug(f"TASKS ASSIGNED: {tasks_to_thread}")     
            
            # cycle through the created keys as the scheduled threads complete
            for task in concurrent.futures.as_completed(tasks_to_thread):
                # This captures the return of the function passed in by self.function
                # Fct output could be iterable, TaskRsult object, or single object/variable
                task_id = tasks_to_thread[task]
                # logging.debug(f"TASK RESULT: {task.result()}")
                
                try:
                    try:
                        object_iterator = iter(task.result())
                        for t in task.result():
                            # This if will allow any function to manually set Task pass/fail conditons
                            if isinstance(t, TaskResult):
                                if t.task_complete is True:
                                    successful_tasks.append(t)
                                else:
                                    failed_tasks.append(t)

                        task_out = TaskResult(task=self.function,
                                                iter_id=task_id,
                                                taskresult=True,
                                                passdata=task.result())

                        successful_tasks.append(task_out)

                    except TypeError as te:
                        # This will run if the output from the given fct is not iterable
                        # This does not indicate a problem
                        logging.debug(f"RUN_PARALLEL: {task_id}: Not iterable: {te}")
                        # This if will allow any function to manually set Task pass/fail conditons
                        # It detects if the fct created a TaskResult object and respects its pass/fail setting
                        if isinstance(task.result(), TaskResult):
                            if task.result().task_complete is True:
                                successful_tasks.append(task.result())
                            else:
                                failed_tasks.append(task.result())
                        else:

                            task_out = TaskResult(task=self.function,
                                                    iter_id=task_id)                          
                            
                            if fail_on_false is True:
                                if task.result() is False:
                                    task_out.task_complete = False
                                    task_out.failure_data = "Function returned False"
                                    failed_tasks.append(task_out)
                                else:
                                    task_out.task_complete = True
                                    task_out.return_data = task.result()
                                    successful_tasks.append(task_out)
                            else:
                                task_out.task_complete = True
                                task_out.return_data = task.result()                                
                                successful_tasks.append(task_out)

                except Exception as e:
                    logging.warning(f"RUN_PARALLEL: Run exception handled: {e}")
                    # This logs an error/exception in the passed in fct. It appends as a failed task 
                    task_out = TaskResult(task=self.function,
                                            iter_id=task_id,
                                            taskresult=False,
                                            faildata=e)
                    failed_tasks.append(task_out)

        self.execution_complete = True

        self.passed_tasks = successful_tasks
        self.failed_tasks = failed_tasks
        
        return self

    def all_pass_ids(self):
        """Get all name of all iter_ids that passed"""

        passed_ids = []
        for pt in self.passed_tasks:
            passed_ids.append(pt.iter_id)

        return passed_ids

    def all_pass_data(self):
        """Get fct output of all iters that passed"""

        passed_data = []
        for pt in self.passed_tasks:
            passed_data.append(pt.return_data)

        return passed_data

    def all_fail_ids(self):
        """Get all name of all iter_ids that failed"""

        failed_ids = []
        for pt in self.failed_tasks:
            failed_ids.append(pt.iter_id)

        return failed_ids

    def all_fail_data(self):
        """Get error message of all iter_ids that failed"""

        failed_data = []
        for pt in self.failed_tasks:
            failed_data.append(pt.failure_data)

        return failed_data

