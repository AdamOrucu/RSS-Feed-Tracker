import sqlite3
import feedparser
import threading
import os
import sys
import time
import smtplib
from email.message import EmailMessage
from app import run_flask
import config


class Post(threading.Thread):
   def __init__(self):
      threading.Thread.__init__(self)
      self.daemon = True
      self._stop_event = threading.Event()
      self.BLOG_URLS = []
      self.to_notify = []
      
      self.server = smtplib.SMTP('smtp.gmail.com', 587)
      self.server.ehlo()
      self.server.starttls()
      self.server.login(config.LOGINNAME, config.LOGINPASSWORD)

   def run(self):
      self.conn = sqlite3.connect('rss.db')
      self.c = self.conn.cursor()
      self.create_table()
      self.post_check(config.POSTCHECKTIME)

   def stop(self):
      self.c.close()
      self.conn.close()
      self._stop_event.set()

   def create_table(self):
      self.c.execute(
          'CREATE TABLE IF NOT EXISTS lastposts(page TEXT, posttitle TEXT, postid TEXT)')
      self.c.execute(
          'CREATE TABLE IF NOT EXISTS pages(page TEXT)')

   def get_pages(self):
      self.c.execute('SELECT * FROM pages')
      pages = self.c.fetchall()
      return [page[0] for page in pages]

   def save_data(self, page, posttitle, postid):
      self.c.execute(
          f'INSERT OR REPLACE INTO lastposts (page, posttitle, postid) VALUES (\"{page}\", \"{posttitle}\", \"{postid}\")')
      self.conn.commit()

   def modify_pages(self, page, delete=False):
      if not delete:
         self.c.execute(f'INSERT INTO pages (page) VALUES (\"{page}\")')
      else:
         self.c.execute(f'DELETE FROM pages WHERE page = \"{page}\"')
      self.conn.commit()

   def get_post(self, page):
      self.c.execute(
          f'SELECT posttitle, postid FROM lastposts WHERE page = \"{page}\"')
      return self.c.fetchone()

   def notify_user(self):
      email = EmailMessage()
      email['Subject'] = 'RSS Feed Update'
      email['From'] = config.LOGINEMAIL
      email['To'] = config.DESTEMAIL

      if self.to_notify != []:
         msg = ""
         for new_post in self.to_notify:
            pg = new_post[0].split('://')[1].split('/feed')[0]
            title = new_post[1]
            link = new_post[2]
            msg += f'<li>{pg.upper()} - <a href="{link}">{title}</a></li>'.format('utf-8')

         email.set_content(f"""\
            <!DOCTYPE html>
            <html>
               <body>
                  <h3>New Posts ({self.to_notify.__len__()})</h3>
                  <h4>
                     <ul>
                        {msg}
                     </ul>
                  </h4>
               </body>
            </html>
            """, subtype='html')
         self.server.send_message(email)
         print('Email sent.')
         self.to_notify = []
      print('End notify')

   def post_exists(self, page):
      feed = feedparser.parse(page)
      posttitle = feed.entries[0].title
      postid = feed.entries[0].id
      posts = self.get_post(page)
      if posts != None:
         if posttitle == posts[0] and postid == posts[1]:
            return True
      self.to_notify.append((page, posttitle, postid))
      self.save_data(page, posttitle, postid)
      return False

   def post_check(self, secs):
      while not self._stop_event.is_set():
         self.BLOG_URLS = self.get_pages()
         for BLOG in self.BLOG_URLS:
            self.post_exists(BLOG)
         time.sleep(secs)
         # print('exi')
         # raise SystemExit()


if __name__ == '__main__':
   try:
      post = Post()
      flask_thread = threading.Thread(target=run_flask)
      flask_thread.daemon = True

      post.start()
      flask_thread.start()
      while True:
         post.notify_user()
         time.sleep(config.NOTIFYTIME)

   except KeyboardInterrupt:
      print('BREAK')
      # post.stop()
      try:
         sys.exit(0)
      except SystemExit:
         os._exit(0)
