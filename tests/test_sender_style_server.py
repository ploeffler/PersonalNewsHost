from io import BytesIO
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from scripts.sender_style import Store, DEFAULT
from scripts.sender_style_server import App, Handler, Server
from scripts.style_preview import policy


class ServerTests(unittest.TestCase):
    def test_reissue_requires_auth_csrf_credentials_and_explicit_paid_consent(self):
        old=self.store.adopt(0,policy({}))['batches'][0]['id']
        body={'batch':old,'allow_paid':True,'allow_uncertain':False}
        self.assertEqual(self.request('/api/reissue',body,cookie=False)[0],401)
        self.assertEqual(self.request('/api/reissue',body,csrf=False)[0],403)
        env={'PNH_STYLE_IMAGE_PROVIDER':'openai','PNH_STYLE_ALLOW_PAID':'true','PNH_STYLE_IMAGE_API_KEY':'fixture'}
        with patch.dict('os.environ',env):
            self.assertEqual(self.request('/api/reissue',{'batch':old,'allow_paid':False})[0],400)
            result=self.request('/api/reissue',body)
            self.assertEqual(result[0],200)
            self.assertEqual(len(result[1]['batches']),2)
            self.assertEqual(self.request('/api/reissue',body)[0],200)
            self.assertEqual(len(self.store.state()['batches']),2)

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=Store(Path(self.temp.name)/'state');self.app=App(self.store,'unit-fixture-password-123',Path(self.temp.name)/'absent.json')
        self.session,self.csrf=self.app.login('unit-fixture-password-123')
    def request(self,path,body=None,cookie=True,csrf=True,origin=True,host='127.0.0.1:8766'):
        handler=object.__new__(Handler);handler.server=SimpleNamespace(app=self.app,server_port=8766)
        handler.path=path;handler.headers={'Host':host};handler.responses=[]
        if cookie:handler.headers['Cookie']='pnh_style='+self.session
        if body is not None:
            raw=json.dumps(body).encode();handler.rfile=BytesIO(raw)
            handler.headers.update({'Content-Type':'application/json','Content-Length':str(len(raw))})
            if origin:handler.headers['Origin']='http://127.0.0.1:8766'
            if csrf:handler.headers['X-CSRF-Token']=self.csrf
        def reply(code,data,kind=None,cookie=None):handler.responses.append((code,data,cookie))
        handler.reply=reply
        handler.do_POST() if body is not None else handler.do_GET()
        return handler.responses[-1]
    def test_authentication_host_and_csrf_gates(self):
        self.assertEqual(self.request('/api/state',cookie=False)[0],401)
        self.assertEqual(self.request('/api/state',host='attacker.example')[0],403)
        for kwargs in ({'csrf':False},{'origin':False},{'cookie':False}):
            code,*_=self.request('/api/draft',{'draft':DEFAULT,'revision':0},**kwargs)
            self.assertIn(code,(401,403))
        self.assertEqual(self.store.state()['revision'],0)
    def test_login_cookie_and_rate_limit(self):
        result=self.request('/api/login',{'password':'unit-fixture-password-123'},cookie=False,csrf=False)
        self.assertEqual(result[0],200);self.assertIn('HttpOnly',result[2]);self.assertIn('SameSite=Strict',result[2])
        for _ in range(8):
            with self.assertRaises(ValueError):self.app.login('wrong')
        with self.assertRaises(ValueError):self.app.login('unit-fixture-password-123')
    def test_first_setup_seed_and_later_restart_preserve_draft(self):
        config=Path(self.temp.name)/'outlet.json';config.write_text(json.dumps({'title':'Bergfunk','private_token':'do-not-copy'}))
        App(self.store,'unit-fixture-password-123',config)
        state=self.store.state();self.assertEqual(state['draft']['name'],'Bergfunk');self.assertNotIn('do-not-copy',str(state))
        self.store.save_draft({**state['draft'],'name':'Bewusster Entwurf'},state['revision'])
        App(self.store,'unit-fixture-password-123',config)
        self.assertEqual(self.store.state()['draft']['name'],'Bewusster Entwurf')
    def test_save_adopt_export_and_conflict(self):
        saved=self.request('/api/draft',{'revision':0,'draft':{**DEFAULT,'name':'Wiesenfunk'}})
        self.assertEqual(saved[0],200)
        self.assertEqual(self.request('/api/draft',{'revision':0,'draft':DEFAULT})[0],409)
        with patch('scripts.sender_style_server.policy',return_value=policy({})):
            result=self.request('/api/adopt',{'revision':1,'allow_paid':False})
        self.assertEqual(result[0],200);self.assertEqual(len(result[1]['batches'][0]['jobs']),14)
        export=self.request('/api/export');self.assertEqual(export[1]['sender_style']['style']['name'],'Wiesenfunk')
        self.assertEqual(self.request('/config.json')[0],404)
        self.assertEqual(self.request('/state/sender-style.sqlite')[0],404)
    def test_url_research_does_not_modify_draft_or_activate(self):
        before=self.store.state()
        with patch('scripts.sender_style_server.analyze',return_value={'suggested_patch':{'colors':['#abcdef']}}):
            self.assertEqual(self.request('/api/research',{'url':'https://fixture.example'})[0],200)
        self.assertEqual(self.store.state(),before)
    def test_private_image_only_after_complete_and_no_path_traversal(self):
        state=self.store.adopt(0,policy({}));job=state['batches'][0]['jobs'][0]['id']
        self.assertEqual(self.request('/images/'+job+'.png')[0],404)
        self.assertEqual(self.request('/images/../../config.json')[0],404)
        self.assertEqual(self.request('/examples/../../config.json')[0],404)
        self.assertEqual(self.request('/api/jobs/'+job,cookie=False)[0],401)
    def test_server_refuses_public_bind(self):
        with self.assertRaises(ValueError):Server(('0.0.0.0',8766),self.app)
    def test_logout_invalidates_server_session(self):
        self.assertEqual(self.request('/api/logout',{})[0],200)
        self.assertEqual(self.request('/api/state')[0],401)

