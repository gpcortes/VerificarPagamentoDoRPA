import os
import platform
import pycamunda.externaltask
import requests.auth
import requests.sessions
import pycamunda.processinst


class worker:
    def __init__(self):
        self.ENG_REST_URL, self.TOPIC, self.WORKER_ID, self.ENG_REST_USERNAME, self.ENG_REST_PASSWORD, self.MAX_TASK_DURATION = self.__load_env()
        self.SESSION = self.__get_auth(self.ENG_REST_USERNAME, self.ENG_REST_PASSWORD)

    def __load_env(self):
        if os.getenv('ENV') != 'production':
            from os.path import join, dirname
            from dotenv import load_dotenv
            dotenv_path = join(dirname(__file__), 'worker.env')
            load_dotenv(dotenv_path)

        ENG_REST_URL = os.getenv('ENG_REST_URL')
        HOST = platform.node()
        TOPIC = os.getenv('TOPIC')
        WORKER_ID = TOPIC + '.' + HOST
        ENG_REST_USERNAME = os.getenv('ENG_REST_USERNAME')
        ENG_REST_PASSWORD = os.getenv('ENG_REST_PASSWORD')
        MAX_TASK_DURATION = os.getenv('MAX_TASK_DURATION')

        return ENG_REST_URL, TOPIC, WORKER_ID, ENG_REST_USERNAME, ENG_REST_PASSWORD, MAX_TASK_DURATION

    def __get_auth(self, username, password):
        session = requests.sessions.Session()
        session.auth = requests.auth.HTTPBasicAuth(
            username=username, password=password)
        return session

    def fetch_tasks(self, topic=None, max_tasks=1, lock_duration=30000):
        
        topic = self.TOPIC if topic is None else topic
        
        fetch_and_lock = pycamunda.externaltask.FetchAndLock(
            url=self.ENG_REST_URL, worker_id=self.WORKER_ID, max_tasks=max_tasks
        )

        fetch_and_lock.add_topic(name=topic, lock_duration=lock_duration)
        fetch_and_lock.session = self.SESSION

        try:
            resp = fetch_and_lock()
            if len(resp) > 0:
                print('Fetched {} tasks.'.format(len(resp)))
            return resp
        except ValueError:
            print('Featching and locking task failed.')
            return None

    def complete_task(self, task_id, variables={}):
        complete = pycamunda.externaltask.Complete(
            url=self.ENG_REST_URL, id_=task_id, worker_id=self.WORKER_ID)
        complete.session = self.SESSION

        for variable in variables:
            complete.add_variable(
                name=variables[variable]['name'], 
                value=variables[variable]['value']
            )

        try:
            return complete()
        except ValueError:
            print('Setting variables failed.')
            return None

    def getTask(self, process_instance_id):
        GetListTasks = pycamunda.task.GetList(
            url=self.ENG_REST_URL, process_instance_id=process_instance_id)

        GetListTasks.session = self.SESSION

        task_id = GetListTasks()[0].id_

        return task_id
