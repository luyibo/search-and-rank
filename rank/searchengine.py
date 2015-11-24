__author__ = 'lyb'
import urllib2
from BeautifulSoup import *
from urlparse import urljoin
import sqlite3


# Create a list of words to ignore
ignorewords={'the':1,'of':1,'to':1,'and':1,'a':1,'in':1,'is':1,'it':1}
class crawler:
  def __init__(self,dbname):
    self.con=sqlite3.connect(dbname)
  def __del__(self):
    self.con.close()

  def dbcommit(self):
    self.con.commit()

  # Auxilliary function for getting an entry id and adding
  # it if it's not present
  def getentryid(self,table,field,value,createnew=True):
    cur=self.con.execute(
    "select rowid from %s where %s='%s'" % (table,field,value))
    res=cur.fetchone()
    if res==None:
      cur=self.con.execute(
      "insert into %s (%s) values ('%s')" % (table,field,value))
      return cur.lastrowid
    else:
      return res[0]


  # Index an individual page
  def addtoindex(self,url,soup):
    if self.isindexed(url):return
    print 'Indexing '+url
    text=self.gettextonly(soup)
    words=self.separatewords(text)
    urlid=self.getentryid('urllist','url',url)
    for i in range(len(words)):
        word=words[i]
        if word in ignorewords:continue
        wordid=self.getentryid('wordlist','word',word)
        self.con.execute('insert into wordlocation(urlid,wordid,location) values(%d,%d,%d)'%(urlid,wordid,i))

  def gettextonly(self,soup):
      v=soup.string
      if v==None:
          c=soup.contents
          resulttext=''
          for t in c:
              subtext=self.gettextonly(t)
              resulttext+=subtext+'\n'
          return resulttext
      else:return v.strip()

  # Seperate the words by any non-whitespace character
  def separatewords(self,text):
      splitter=re.compile('\\W*')
      return [s.lower() for s in splitter.split(text) if s!='']



  # Return true if this url is already indexed
  def isindexed(self,url):
    u=self.con.execute('select rowid from urllist where url="%s"'%url).fetchone()
    if u!=None:
        v=self.con.execute('select * from wordlocation where urlid=%d'%u[0]).fetchone()
        if v!=None:return True
    return False
  # Add a link between two pages
  def addlinkref(self,urlFrom,urlTo,linkText):
   pass
  def crawl(self,pages,depth=4):
      for i in range(depth):
          print 1
          newpages={}
          for page in pages:
              try:
                  c=urllib2.urlopen(page)
              except:
                  print "could not open %s"%page
                  continue
              soup=BeautifulSoup(c.read())
              self.addtoindex(page,soup)
              links=soup('a')
              for link in links:
                  if ('href' in dict(link.attrs)):
                      url=urljoin(page,link['href'])
                      if url.find("'")!=-1:continue
                      url=url.split('#')[0]
                      if url[0:4]=='http' and not self.isindexed(url):
                          newpages[url]=1
                      linkText=self.gettextonly(link)
                      self.addlinkref(page,url,linkText)
              self.dbcommit()
          pages=newpages
  def createindextables(self):
      self.con.execute('create table urllist(url)')
      self.con.execute('create table wordlist(word)')
      self.con.execute('create table wordlocation(urlid,wordid,location)')
      self.con.execute('create table link(fromid integer,toid integer)')
      self.con.execute('create table linkwords(wordid,linkid)')
      self.con.execute('create index wordidx on wordlist(word)')
      self.con.execute('create index urlidx on urllist(url)')
      self.con.execute('create index wordurlidx on wordlocation(wordid)')
      self.con.execute('create index urltoidx on link(toid)')
      self.con.execute('create index urlfromidx on link(fromid)')
      self.dbcommit()
crawler=crawler('searchindex.db')
pages=['http://www.apple.com']
crawler.crawl(pages)