import requests, json, getpass

class Session:
    
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.token    = None

    def do(self, request_function, url, data=None, loggedin_required=True):
        assert not loggedin_required or self.token is not None, "must login first"
        resp = request_function(self.endpoint+"/"+url, json=data, 
                             headers={'Content-Type':'application/json',
                                      'Mooc-Token': self.token})
        if resp.status_code!=200:
            c = eval(resp.content)
            if "traceback" in c:
                traceback = c["traceback"]
                e = ValueError(c["error"]+"\n\ntraceback:\n"+traceback)
                raise e
            else:
                msg = "\n--\n".join([str(i) for i in [resp.content, resp.headers, resp.text, resp.reason]])
                raise ValueError(msg)
        return resp

    def do_post(self, url, data=None, loggedin_required=True):
        return self.do(requests.post, url, data, loggedin_required)

    def do_get(self, url, data=None, loggedin_required=True):
        return self.do(requests.get, url, data, loggedin_required)    

    def do_put(self, url, data=None, loggedin_required=True):
        return self.do(requests.put, url, data, loggedin_required)        
    
    def do_delete(self, url, data=None, loggedin_required=True):
        return self.do(requests.delete, url, data, loggedin_required)        
    
    def do_head(self, url, data=None, loggedin_required=True):
            return self.do(requests.head, url, data, loggedin_required)        

    def login(self, user=None, pwd=None):
        if user is None:
            user = input("username: ")
        if pwd is None:
            pwd = getpass.getpass("password: ")

        data = {"user_id": user, "user_pwd": pwd}
        resp = self.do_post("login", data, loggedin_required=False)
        self.token = eval(resp.content)["Mooc-Token"]
        self.user = user
        return self
        
    def create_user(self, user, pwd, name):
        data = {"user_id": user, "user_name": name, "user_pwd": pwd}
        self.do_post("users", data)

    def get_user(self, user):
        resp = self.do_get("users/%s"%user)
        if resp.status_code==200:
            return eval(resp.content.decode())

    def delete_user(self, user_id):
        self.do_delete("users/%s"%user_id)

    def user_exists(self, user_id):
        resp = self.do_get("users/%s/exists"%(user_id))
        if resp.status_code==200:
            return eval(resp.content.decode())["result"]==str(True)

    def create_course(self, cspec, owner=""):
        cspec = json.dumps(cspec)
        data = {"course_spec": cspec, "owner": owner}
        self.do_post("courses", data)

    def update_course(self, cspec):
        course_id = cspec["course_id"]
        cspec = json.dumps(cspec)
        data = {"course_spec": cspec}
        self.do_put("courses/%s"%course_id, data)
        
    def get_course(self, course_id):
        resp = self.do_get("courses/%s"%course_id)
        if resp.status_code==200:
            return eval(resp.content.decode())

    def course_exists(self, course_id):
        resp = self.do_get("courses/%s/exists"%(course_id))
        if resp.status_code==200:
            return eval(resp.content.decode())["result"]==str(True)

    def delete_course(self, course_id):
        self.do_delete("courses/%s"%course_id)

    def create_user_course(self, course_id, user_id, start_date):
        data = {"user_id": user_id, "course_id": course_id, "start_date": start_date}
        self.do_post("users/%s/courses"%user_id, data)
        
    def delete_user_course(self, course_id, user_id):
        user_id = user_id if user_id is not None else self.user
        self.do_delete("users/%s/courses/%s"%(user_id, course_id))
        
    def get_user_course(self, course_id, user_id=None):
        user_id = user_id if user_id is not None else self.user
        resp = self.do_get("users/%s/courses/%s"%(user_id, course_id))
        if resp.status_code==200:
            return eval(resp.content.decode())

    def user_course_exists(self, course_id, user_id=None):
        user_id = user_id if user_id is not None else self.user
        resp = self.do_get("users/%s/courses/%s/exists"%(user_id, course_id))
        if resp.status_code==200:
            return eval(resp.content.decode())["result"]==str(True)

    def set_grader(self, course_id, lab_id, task_id, grader_source, grader_function_name):
        data = {
                  "grader_source": grader_source,
                  "grader_function_name": grader_function_name
                }
        self.do_post("courses/%s/labs/%s/tasks/%s/grader"%(course_id, lab_id, task_id), data)

    def get_grader(self, course_id, lab_id, task_id):
        resp = self.do_get("courses/%s/labs/%s/tasks/%s/grader"%(course_id, lab_id, task_id))
        if resp.status_code==200:
            return json.loads(resp.content.decode())

    def submit_task(self, course_id, lab_id, task_id, submission_content, user_id=None):
        user_id = user_id if user_id is not None else self.user
        if type(submission_content)!=dict:
            raise ValueError("submission must be a dictionary")
        data = {"submission_content": submission_content}
        resp = self.do_post("users/%s/courses/%s/labs/%s/tasks/%s"%(user_id, course_id, lab_id, task_id), data)
        if resp.status_code==200:
           return eval(resp.content.decode()) 

