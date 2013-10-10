#!/usr/bin/env python
# encoding: utf-8
# author: cookpan001
import sys
import logging
import time
import mimetypes
import urllib
import urllib2
"""
oauth2 client
"""
class OAuth2(object):
    ACCESS_TOKEN_URL = "https://auth.sina.com.cn/oauth2/access_token"
    AUTHORIZE_URL = "https://auth.sina.com.cn/oauth2/authorize"

    def __init__(self,app_key, app_secret, call_back_url):
        self.version = 1.0
        self.app_key = app_key
        self.app_secret = app_secret
        self.call_back_url = call_back_url

    #display = default|mobile|popup
    def authorize(self,response_type = "code",display = "default",state = ""):
        data = {"client_id":self.app_key,
                "redirect_uri":self.call_back_url,
                "response_type":response_type,
                "display":display}
        if len(state) > 0:
            data["state"] = state
        return OAuth2.AUTHORIZE_URL + "?" + urllib.urlencode(data)

    #grant_type = authorization_code|refresh_token
    def access_token(self,grant_type = "authorization_code",code = "",refresh_token = ""):
        data = {"client_id":self.app_key,
                "client_secret":self.app_secret,
                "grant_type":grant_type}
        if grant_type == "authorization_code":
            data["code"] = code
            data["redirect_uri"] = self.call_back_url
        elif grant_type == "refresh_token":
            data["refresh_token"] = refresh_token
        try:
            request = urllib2.Request(OAuth2.ACCESS_TOKEN_URL)
            response = urllib2.urlopen(request,urllib.urlencode(data))
            return response.read()
        except urllib2.HTTPError,e:
            return e.read()
        except urllib2.URLError,e:
            return e.read()
"""
All the responses will be a Response object
"""
class Response(object):
    BLOCK_SIZE = 8192
    def __init__(self,response):
        self.response = response
    """
    return a HTTPMessage object
    """
    def headers(self):
        if hasattr(self.resopnse,"info"):
            return self.response.info()
        elif hasattr(self.resopnse,"msg"):
            return self.resopnse.msg()

    """
    Get the content of response ,optimized for big size resopnse.
    data() return a generator. Developer can use this method like this:

    for content in Response.data():
        print content
    """
    def data(self):
        while True: 
            block = self.response.read(Response.BLOCK_SIZE) 
            if block: 
                yield block 
            else: 
                return

    def read(self):
        return self.response.read()

    def __str__(self):
        return self.response.read()
"""
The vdisk(weipan) client.
"""
class Client(object):
    log = logging.getLogger('api_client')
    API_URL = 'https://api.weipan.cn/2/'
    WEIBO_URL = 'https://api.weipan.cn/weibo/'
    UPLOAD_HOST = 'upload-vdisk.sina.com.cn'
    CONTENT_SAFE_URL = 'https://'+UPLOAD_HOST+'/2/'
    version = 1.0

    def __init__(self,root = "basic"):
        self.timeout = 10
        self.python_version_is_bigger_than_2_4 = float(sys.version[:3]) > 2.4
        self.root = root

    def setRoot(self,root):
        self.root = root

    def get(self, host, api, queries={}):
        try:
            if isinstance(api, unicode):
                api = api.encode('utf-8')
            else:
                api = str(api)
            url = host.strip('/') + '/' + urllib.quote(api.strip('/'))
            queries = self.encode_queries(queries)
            request = urllib2.Request('%s?%s' % (url, queries))
            # set timeout.
            if self.python_version_is_bigger_than_2_4:
                response = urllib2.urlopen(request, timeout=self.timeout)
            else:
                # http://stackoverflow.com/questions/2084782/timeout-for-urllib2-urlopen-in-pre-python-2-6-versions
                import socket
                socket.setdefaulttimeout(self.timeout)
                response = urllib2.urlopen(request)
            return Response(response)
        except urllib2.HTTPError,e:
            return e.read()
        except urllib2.URLError,e:
            return e.read()

    def post(self, host, api, data=[], files=[]):
        try:
            if isinstance(api, unicode):
                api = api.encode('utf-8')
            else:
                api = str(api)
            url = host.strip('/') + '/' + api.strip('/')
            if isinstance(data, dict):
                data = data.items()
            content_type, body = self.encode_multipart_formdata(data, files)
            request = urllib2.Request(url, data=body)
            request.add_header('Content-Type', content_type)
            request.add_header('Content-Length', str(len(body)))
            if self.python_version_is_bigger_than_2_4:
                response = urllib2.urlopen(request, timeout=self.timeout)
            else:
                import socket
                socket.setdefaulttimeout(self.timeout)
                response = urllib2.urlopen(request)
            return Response(response)
        except urllib2.HTTPError,e:
            return e.read()
        except urllib2.URLError,e:
            return e.read()
    # used by non GET or POST method. such as PUT
    def request(self, method,host, api, data, headers = {}, use_safe = True):
        import httplib
        if isinstance(api, unicode):
            api = api.encode('utf-8')
        else:
            api = str(api)
        if isinstance(data, dict):
            data = self.encode_queries(data)
        try:
            if use_safe:
                conn = httplib.HTTPSConnection(host)
            else:
                conn = httplib.HTTPConnection(host)
            conn.request(method,api,data,headers)
            return Response(conn.getresponse())
        except httplib.HTTPException,e:
            print e
            return e.read()

    def get_content_type(self, filename):
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

    def encode_multipart_formdata(self, fields, files):
        """
        fields is a sequence of (name, value) elements for regular form fields.
        files is a sequence of (name, filename, value) elements for data to be uploaded as files
        Return (content_type, body) ready for httplib.HTTP instance
        """
        BOUNDARY = '----------%s' % hex(int(time.time() * 1000))
        CRLF = '\r\n'
        L = []
        for (key, value) in fields:
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"' % str(key))
            L.append('')
            if isinstance(value, unicode):
                L.append(value.encode('utf-8'))
            else:
                L.append(value)
        for (key, filename, value) in files:
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (str(key), str(filename)))
            L.append('Content-Type: %s' % str(self.get_content_type(filename)))
            L.append('Content-Length: %d' % len(value))
            L.append('')
            L.append(value)
        L.append('--' + BOUNDARY + '--')
        L.append('')

        body = CRLF.join(L)
        content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
        return content_type, body

    def encode_queries(self, queries={}, **kwargs):
        queries.update(kwargs)
        args = []
        for k, v in queries.iteritems():
            if isinstance(v, unicode):
                qv = v.encode('utf-8')
            else:
                qv = str(v)
            args.append('%s=%s' % (k, urllib.quote(qv)))
        return '&'.join(args)

    def account_info(self,access_token):
        data = self.get(Client.API_URL,
                        'account/info',
                        {"access_token":access_token})
        return data

    def metadata(self,access_token,path):
        data = self.get(Client.API_URL,
                        'metadata/' + self.root + '/' + path,
                         {"access_token":access_token})
        return data

    def delta(self,access_token,cursor = ''):
        param = {"access_token":access_token}
        if len(cursor) > 0:
            param['cursor'] = cursor
        data = self.get(Client.API_URL,
                        'delta/' + self.root,
                         param)
        return data

    def files(self,access_token,path,rev = ''):
        param = {"access_token":access_token}
        if len(rev) > 0:
            param['rev'] = rev
        data = self.get(Client.API_URL,
                        'files/' + self.root + "/" + path,
                         param)
        return data

    def revisions(self,access_token,path):
        data = self.get(Client.API_URL,
                        'revisions/' + self.root + "/" + path,
                         {"access_token":access_token})
        return data
    #files = {"filename":filename,"content":"file content"}
    def files_post(self,access_token,path,files,overwrite = "true",sha1 = "",size = "", parent_rev = ""):
        param = {
                 "access_token":access_token,
                 "overwrite":overwrite
                 }
        if len(sha1) > 0:
            param["sha1"] = sha1
        if len(size) > 0:
            param["size"] = size
        if len(parent_rev) > 0:
            param["parent_rev"] = parent_rev
        queries = self.encode_queries(param)
        data = self.post(Client.CONTENT_SAFE_URL,
                        'files/'+self.root+"/"+path+"?"+queries,
                         [],
                         [("file",files["filename"],files["content"])])
        return data
    """
    content should be a file object or file raw content, such as: open("./filename","rb"), "rb" is prefered.
    """
    def files_put(self,access_token,path,content,overwrite = "true",sha1 = "",size = "", parent_rev = ""):
        param = {
                 "access_token":access_token,
                 "overwrite":overwrite
                }
        if len(sha1) > 0:
            param["sha1"] = sha1
        if len(size) > 0:
            param["size"] = size
        if len(parent_rev) > 0:
            param["parent_rev"] = parent_rev
        data = self.request(
                        method="PUT",
                        host=Client.UPLOAD_HOST,
                        api='/2/files_put/'+self.root+"/"+path+"?"+self.encode_queries(param),
                        data=content)
        return data
    # 公开分享
    def shares(self,access_token,path,cancel = "false"):
        data = self.post(Client.API_URL,
                        'shares/'+self.root+"/"+path,
                         {"access_token":access_token,
                          "cancel":cancel
                          })
        return data

    def restore(self,access_token,path,rev = ""):
        param = {"access_token":access_token,
                 "path":path
                }
        if len(rev) > 0:
            param['rev'] = rev
        data = self.post(Client.API_URL,
                         'restore/'+self.root+"/"+path,
                         {"access_token":access_token})
        return data

    def search(self,access_token,path,query,file_limit = 1000,include_deleted = "false"):
        data = self.get(Client.API_URL,
                        'search/'+self.root+"/"+path,
                         {"access_token":access_token,
                          "path":path,
                          "query":query,
                          "file_limit":file_limit,
                          "include_deleted":include_deleted
                          })
        return data

    def copy_ref(self,access_token,path):
        data = self.post(Client.API_URL,
                         'copy_ref/'+self.root+"/"+path,
                          {"access_token":access_token,
                           "path":path})
        return data

    def media(self,access_token,path):
        data = self.get(Client.API_URL,
                        'media/'+self.root+"/"+path,
                         {"access_token":access_token,
                          "path":path})
        return data
    #s:60x60,m:100x100,l:640x480,xl:1027x768
    def thumbnails(self,access_token,path,size):
        data = self.get(Client.API_URL,
                        'thumbnails/'+self.root+"/"+path,
                         {"access_token":access_token,
                          "path":path,
                          "size":size})
        return data

    def fileops_copy(self,access_token,to_path,from_path = "",from_copy_ref = ""):
        param = {"access_token":access_token,
                 "root":self.root,
                 "to_path":to_path
                }
        if len(from_path) > 0:
            param['from_path'] = from_path
        if len(from_copy_ref) > 0:
            param['from_copy_ref'] = from_copy_ref
        data = self.post(Client.API_URL,
                         'fileops/copy',
                         param)
        return data

    def fileops_delete(self,access_token,path):
        data = self.post(Client.API_URL,
                         'fileops/delete',
                         {"access_token":access_token,
                          "root":self.root,
                          "path":path
                          })
        return data

    def fileops_move(self,access_token,from_path = "",to_path = ""):
        param = {"access_token":access_token,
                 "root":self.root
                 }
        if len(from_path) > 0:
            param['from_path'] = from_path
        if len(to_path) > 0:
            param['to_path'] = to_path
        data = self.post(Client.API_URL,
                         'fileops/move',
                         param)
        return data

    def fileops_create_folder(self,access_token,path):
        data = self.post(Client.API_URL,
                         'fileops/create_folder',
                         {"access_token":access_token,
                          "root":self.root,
                          "path":path
                          })
        return data

    def shareops_media(self,access_token,from_copy_ref):
        data = self.get(Client.API_URL,
                        'shareops/media', 
                        {"access_token":access_token,
                         "from_copy_ref":from_copy_ref})
        return data
