import xml.dom.minidom
import os
import socket
import json
import random
import datetime
import smtplib
from email.mime.text import MIMEText
import time
import ssl
import flask
from flask import Flask,redirect,render_template,session,url_for
import requests

def get_random_name():
   adjs=['blue','yellow','green','red','crazy','happy','nice','sad','cool','hot']
   nouns=['horse','cat','dog','monkey','car','bike','plane','tomato','apple','banana']
   return "%s-%s" % (random.choice(adjs),random.choice(nouns))
def get_pin():
   return str(random.randint(0,9999)).zfill(4)
def add_alias(a,name,c):
   alias={x['name']:int(y['alias']) for y in x['aliases'] if y.get('alias','').isdigit() for x in a}
   newalias=min(alias.values())-1
   r = requests.post("https://%s/api/admin/configuration/v1/conference_alias/" % pexip_server, auth=('admin', pexip_password),data=json.dumps({'alias':newalias,'conference':c}))
   r = requests.post("https://%s/api/admin/configuration/v1/conference_alias/" % pexip_server, auth=('admin', pexip_password),data=json.dumps({'alias':name,'conference':c}))
   r = requests.post("https://%s/api/admin/configuration/v1/conference_alias/" % pexip_server, auth=('admin', pexip_password),data=json.dumps({'alias':"%s@%s" % (name,pexip_url),'conference':c}))
   return newalias

def pexip_create_room():
   l=[]
   nx="/api/admin/configuration/v1/conference/"
   while nx:
      r = requests.get("https://%s%s" % (pexip_server,nx), auth=('admin', pexip_password))
      j= json.loads(r.text)
      nx=j['meta']['next']
      l+=j['objects']
   while True:
      n=get_random_name()
      d={'name': n, 'service_type': 'conference','pin':get_pin(),'allow_guests':True,'guest_pin':get_pin(),'description': "ad-hoc room created: %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
      r = requests.post("https://%s/api/admin/configuration/v1/conference/" % pexip_server, auth=('admin', pexip_password),data=json.dumps(d))
      if r.status_code==201: break
   c=r.headers['location']
   a=add_alias(l,n,c)
   r = requests.get(c, auth=('admin', pexip_password))
   rd=json.loads(r.text)
   return (rd['name'],rd['pin'],a)

def sendemail(l,m):
  try:
   msg = MIMEText(m)
   msg['Subject'] = 'Meeting invite'
   msg['From'] = smtp_sender
   msg['To'] = ",".join(l)
   s = smtplib.SMTP(smtp_server)
   s.sendmail(smtp_sender, l, msg.as_string())
   s.quit()
  except:
    pass
  return None

pexip_server=os.environ.get('pexip_server','')
pexip_password=os.environ.get('pexip_password','')
pexip_url=os.environ.get('pexip_url','')
cas_server=os.environ.get('cas_server','')
smtp_server=os.environ.get('smtp_server','')
smtp_sender=os.environ.get('smtp_sender','')

app = Flask(__name__)

@app.route('/')
def route_root():
   t=flask.request.args.get('ticket','')
   if t:
      x=requests.get("https://%s/serviceValidate?service=https://%s&ticket=%s" % (cas_server,socket.gethostname(),t))
      dom = xml.dom.minidom.parseString(x.text.encode('utf-8'))
      try:
         casuser=dom.getElementsByTagName('cas:user')[0].childNodes[0].nodeValue
      except:
         return redirect("https://%s/?service=https://%s" % (cas_server,socket.gethostname()))
      return redirect("https://%s/success?room=%s&pin=%s&alias=%s" % ((socket.gethostname(),)+pexip_create_room()))
   else:
      return redirect("https://%s/?service=https://%s" % (cas_server,socket.gethostname())) 

@app.route('/success',methods=['GET', 'POST'])
def success():
   if flask.request.method == 'POST':
     name=flask.request.form['name']
     message=flask.request.form['message']
     pin=session['pin']
     room=session['room']
     l=message.split(',')
     sendemail(l,"https://%s/webapp/?conference=%s&pin=%s&join=1\naccess code: %s" % (pexip_url,room,pin,session['alias']))
     return render_template('wait2.html',pin=pin,room=room,url=pexip_url,name=name)
   else: 
     pin=flask.request.args.get('pin','')
     room=flask.request.args.get('room','')
     alias=flask.request.args.get('alias','')
     session['pin']=pin
     session['room']=room
     session['alias']=alias
     return render_template('wait.html')

@app.route('/wait')
def wait():
   pin=flask.request.args.get('pin','')
   room=flask.request.args.get('room','')
   while True:
      x=requests.post("https://%s/api/client/v2/conferences/%s/request_token" % (pexip_url,room),headers={'pin':pin},data={"display_name": "Pexip-bot"})
      if x.status_code==200:
         return json.dumps({'Done':True})
      time.sleep(3)

if __name__ == '__main__':
   app.secret_key = os.urandom(24)
   try:
      ctxt=ssl.SSLContext(ssl.PROTOCOL_SSLv23)
      h=socket.gethostname()
      ctxt.load_cert_chain("/etc/letsencrypt/live/%s/cert.pem" % h,"/etc/letsencrypt/live/%s/privkey.pem" % h)
      ctxt.options|=ssl.OP_NO_SSLv2
      ctxt.options|=ssl.OP_NO_SSLv3
      app.run(host='0.0.0.0',port=443,ssl_context=ctxt)
   except:
      app.run(host='0.0.0.0',port=443,ssl_context='adhoc')