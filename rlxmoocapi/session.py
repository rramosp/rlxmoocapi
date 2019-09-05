import requests, json, getpass, inspect
from IPython.core.display import display, HTML

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

    def login(self, user_id=None, pwd=None, course_id=None, lab_id=None):
        if user_id is None:
            user_id = input("username: ")
        if pwd is None:
            pwd = getpass.getpass("password: ")

        data = {"user_id": user_id, "user_pwd": pwd}
        resp = self.do_post("login", data, loggedin_required=False)
        self.token = eval(resp.content)["Mooc-Token"]
        self.user_id = user_id

        if course_id is not None:
            self.course = self.get_user_course(course_id)
        self.course_id = course_id
        self.lab_id = lab_id

        return self
        
    def create_user(self, user_id, pwd, user_name):
        data = {"user_id": user_id, "user_name": user_name, "user_pwd": pwd}
        self.do_post("users", data)

    def get_user(self, user_id):
        resp = self.do_get("users/%s"%user_id)
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
        user_id = user_id if user_id is not None else self.user_id
        self.do_delete("users/%s/courses/%s"%(user_id, course_id))
        
    def get_user_course(self, course_id, user_id=None):
        user_id = user_id if user_id is not None else self.user_id
        resp = self.do_get("users/%s/courses/%s"%(user_id, course_id))
        if resp.status_code==200:
            return eval(resp.content.decode())

    def user_course_exists(self, course_id, user_id=None):
        user_id = user_id if user_id is not None else self.user_id
        resp = self.do_get("users/%s/courses/%s/exists"%(user_id, course_id))
        if resp.status_code==200:
            return eval(resp.content.decode())["result"]==str(True)

    def set_grader(self, course_id, lab_id, task_id, 
                   grader_source, grader_function_name,
                   source_functions_names, source_variables_names):
        data = {
                  "grader_source": grader_source,
                  "grader_function_name": grader_function_name,
                  "source_functions_names": source_functions_names,
                  "source_variables_names":source_variables_names
                }
        self.do_post("courses/%s/labs/%s/tasks/%s/grader"%(course_id, lab_id, task_id), data)

    def get_grader(self, course_id, lab_id, task_id):
        resp = self.do_get("courses/%s/labs/%s/tasks/%s/grader"%(course_id, lab_id, task_id))
        if resp.status_code==200:
            return json.loads(resp.content.decode())

    def default_course_lab(self, course_id, lab_id):
        course_id = course_id or self.course_id
        lab_id    = lab_id or self.lab_id
        assert course_id is not None, "must set course_id"
        assert lab_id is not None, "must set lab_id"
        return course_id, lab_id

    def get_grader_source_names(self, course_id=None, lab_id=None, task_id=None):
        course_id, lab_id = self.default_course_lab(course_id, lab_id)
        resp = self.do_get("courses/%s/labs/%s/tasks/%s/grader_source_names"%(course_id, lab_id, task_id))
        if resp.status_code==200:
            return json.loads(resp.content.decode())

    def submit_task(self, namespace, course_id=None, lab_id=None, task_id=None, user_id=None,
                    display_html=True):
        """
        call this function with namespace=globals()
        """
        user_id = user_id if user_id is not None else self.user_id
        course_id, lab_id = self.default_course_lab(course_id, lab_id)

        source = self.get_grader_source_names(course_id, lab_id, task_id)
        functions = {f: inspect.getsource(namespace[f]) for f in source['source_functions_names']}
        variables = {v: namespace[v] for v in source['source_variables_names']}
        submission_content = { 'source_functions': functions,
                               'source_variables': variables}

        data = {"submission_content": submission_content}
        resp = self.do_post("users/%s/courses/%s/labs/%s/tasks/%s"%(user_id, course_id, lab_id, task_id), data)
        if resp.status_code==200:
           r = eval(resp.content.decode()) 
           if display_html:
                s = """
                <h2>%s submitted</h2>
                <p/><p/>
                <h3><font color="blue">your grade is %s</font></h3>
                <p/><p/>
                %s
                <p/><p/>
                <div style="font-size:10px"><b>SUBMISSION CODE</b> %s</div>

                """%("task_01", str(r["grade"]), r["message"], r["submission_stamp"])
                display(HTML(s))               
           return r

    def run_grader_locally(self, grader_function_name, source_functions_names, source_variables_names, namespace):
        functions = {f: eval("inspect.getsource(%s)"%f, namespace) for f in source_functions_names}
        variables = {v: namespace[v] for v in source_variables_names}
        return namespace[grader_function_name](functions, variables)

