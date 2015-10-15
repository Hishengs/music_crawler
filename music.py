#!/usr/bin/ 
# -*- coding: utf-8 -*-
import os,re,json,requests,pymysql,datetime,re,math
from multiprocessing import Pool,Lock,Value
from bs4 import BeautifulSoup

#音乐类
class Music(object):
	#初始化
	def __init__(self):
		#连接数据库
		self.__conn=pymysql.connect(host='localhost',user='root',passwd='123456',db='netease_music',port=3306,charset='utf8')
		self.__header = {
		    'Host': 'music.163.com',
		    'Proxy-Connection': 'keep-alive',
		    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.76 Safari/537.36',
		    'Content-Type': 'application/x-www-form-urlencoded',
		    'Accept': '*/*',
		    'Referer': 'http://music.163.com',
		    'Accept-Encoding': 'gzip, deflate, sdch',
		    'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4',
		    'Cookie': 'visited=true; _ntes_nuid=d9d2b31ec03fbea34f79bca0dd66a268; P_INFO=hishengjpr@163.com|1444787345|1|lofter|00&99|gud&1444551405&exchange#gud&440300#10#0#0|137215&1||hishengjpr@163.com; NTES_PASSPORT=IQjcjlJrjqQTVuPX5StuP5IIzQVFZs5rmuAfgeeUYjTdYtclYUOmhkZuWiAgat2w59Yt1O0c6B357T50N8LMHUMUgZCNUeZDnnz.oPOIFTQpD; JSESSIONID-WYYY=76aed175e59cef4cb9b04d021f8e4aa3b53468bd7ac26a0202ed567ec2de6de354f61172eb568e4f1f9fd26cca07244f02e4b5bd5a9c05cf144cd1bc7d233c0282e47014f1e42c5c1af10f65de63c914328a99d03d0a891de3b20066e57491604cd96655e8cd3a3fa8c9a5c7fdaaf18c30c0f4a41bd17a2ea8b3d38e91a11b2249f3d0ed%3A1444879917030; _iuqxldmzr_=25; __utma=94650624.145050166.1444820695.1444836333.1444877989.3; __utmb=94650624.4.10.1444877989; __utmc=94650624; __utmz=94650624.1444820695.1.1.utmcsr=heysoo.com|utmccn=(referral)|utmcmd=referral|utmcct=/Index/index.html'
		}
		#默认资源目录路径
		self.__data_path = 'D:\workspace\python\music163\data'
	#读取文件
	def read_file(self,path):
		with open(path,'r',encoding="utf-8") as f:
			return f.read()
	#将文件保存到本地
	def save_file(self,data,path):
		obj = open(path,'wb')
		obj.write(data)
		obj.close()
	#check 歌曲是否已存在
	def check_song_existed(self,song_id):
		try:
			with self.__conn.cursor() as cursor:
				sql = "SELECT * FROM hs_song WHERE song_id = %s"
				result = cursor.execute(sql,(song_id))
				self.__conn.commit()
				cursor.close()
				if result:
					return True
				else:
					return False
		except  Exception :
			self.__conn.close()
			raise
	#将歌曲信息保存到数据库
	def save_song(self,song_info):
		try:
			with self.__conn.cursor() as cursor:
				if self.check_song_existed(song_info['id']) == False :
					sql = "INSERT INTO hs_song (song_id,song_name,song_singer,song_mp3_url,song_pic_url) VALUES (%s, %s , %s , %s , %s)"
					cursor.execute(sql,(song_info['id'],song_info['name'],song_info['artists'][0]['name'],song_info['mp3Url'],song_info['album']['blurPicUrl']))
					self.__conn.commit()
					cursor.close()
					return True
				else:
					print('歌曲已存在')
					return False
			#print(song_info['id'],song_info['name'],song_info['artists'][0]['name'],song_info['mp3Url'],song_info['artists'][0]['picUrl'])
		except  Exception :
			raise
			self.__conn.close()
			return False

	#通过id列表收集歌曲信息
	#params包括：1.url_prefix前缀 2.header
	def crawl_song_info_by_song_lists(self,song_lists,params):
		start_time = datetime.datetime.now() #记录爬取起始时间
		song_count = 0 #记录爬取的歌曲数目
		for id in song_lists:
			song_id = str(id)
			ids = '["'+str(song_id)+'"]' #这个参数暂不造素干嘛的
			#构造url,limit,offset其实没用
			music163_url = params['url_prefix'] + '?id=' + song_id + '&ids=' + ids + '&limit=' + str(params['limit']) + '&offset=' + str(params['offset'])
			try:
				request = requests.get(music163_url,headers=params['headers'])
				if request.status_code == 200:
					content = json.loads(request.text)
					if content['songs']:
						for item in content['songs']:
							if self.save_song(item): #将歌曲信息保存到数据库
								song_count += 1
								end_time = datetime.datetime.now()
								spend_time = (end_time-start_time).seconds
								num_per_sec = song_count / spend_time
								print('已抓取 ',song_count,' 条歌曲信息，成功保存到数据库！','花费 ',spend_time,' 秒，平均 %.5f' % num_per_sec,' 条/秒')
							else :
								continue
					else :
						print('当前抓取歌曲ID: ',song_id,'，歌曲不存在！')
				else:
					print('连接失败，状态码：',request.status_code)
			except:
				raise
				print('无法打开该网址...')
				conn.close()
				continue

	#多进程-通id列表爬取歌曲信息
	def mul_crawl_song_info_by_song_lists(self,process_num,song_lists,params):
		if __name__=='__main__':
			total_songs_num = len(song_lists) #歌曲列表的总歌曲数
			if total_songs_num > process_num:
				#多进程
				p = Pool(process_num)
				step = math.ceil(total_songs_num/process_num) #步长
				print('step:',step)
				right = 0
				for i in range(process_num):
					left = right
					right = (i*step)+step
					if right > total_songs_num:
						right = total_songs_num 
					print('No.',i,'=>left:',left,',right:',right)
					p.apply_async(self.crawl_song_info_by_song_lists, args=(song_lists[left:right],params))
				p.close()
				p.join()
			else :
				self.crawl_song_info_by_song_lists(song_lists,params)
		else:
			print('不是主进程，即将退出...')
			exit()

	#读取文件的id列表
	def get_song_lists_by_filename(self,filename):
		path = self.__data_path + '\\singer\\' + filename + '.html'
		data = self.read_file(path)
		sp = BeautifulSoup(data,"html.parser") #通过BeautifulSoup处理html
		patern = '/song\?id=(\d*)' #正则提取所有歌曲id
		c_song = re.compile(patern)
		all_links = sp.find_all('a')
		song_lists = []
		for link in all_links:
			if type(link.get('href')) == type("hello"): 
				res = c_song.match(link.get('href'))
				if res:
					song_lists.append(res.group(1)) #提取id
				else :
					del link
		#将id保存为文件到本地
		try:
			self.save_file(str(song_lists).encode('utf-8'),path=self.__data_path + '\\singer\\'+filename+'_id.html')
		except  Exception :
			print('保存歌曲id列表到文件失败！')

		return song_lists


#########################Music class end######################################

#########################Main#################################################
headers = {
	    'Host': 'music.163.com',
	    'Proxy-Connection': 'keep-alive',
	    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.76 Safari/537.36',
	    'Content-Type': 'application/x-www-form-urlencoded',
	    'Accept': '*/*',
	    'Referer': 'http://music.163.com',
	    'Accept-Encoding': 'gzip, deflate, sdch',
	    'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4',
	    'Cookie': 'visited=true; _ntes_nuid=d9d2b31ec03fbea34f79bca0dd66a268; P_INFO=hishengjpr@163.com|1444787345|1|lofter|00&99|gud&1444551405&exchange#gud&440300#10#0#0|137215&1||hishengjpr@163.com; NTES_PASSPORT=IQjcjlJrjqQTVuPX5StuP5IIzQVFZs5rmuAfgeeUYjTdYtclYUOmhkZuWiAgat2w59Yt1O0c6B357T50N8LMHUMUgZCNUeZDnnz.oPOIFTQpD; playerid=68824805; __utma=94650624.145050166.1444820695.1444902182.1444904566.6; __utmc=94650624; __utmz=94650624.1444904566.6.2.utmcsr=localhost|utmccn=(referral)|utmcmd=referral|utmcct=/test/test.html; JSESSIONID-WYYY=f9052082f5dbfe641a2f1f287c140cbc6ed886080f288d5aef66dacdb86c6cca9e5fde53ef9557dbca7d6727a73738811eef38084fdb8c1e41ddc7ca018a5441814f48cbe7dcbc88ecd8da826e618cab4ff496f1929aa31a322f800ac0275b2f018534a544128fedfdbab77dba3fa6c9ca9bca50244312e81737582b284b0156e598663f%3A1444918212893; _iuqxldmzr_=25'
	}
params = {'url_prefix':'http://music.163.com/api/song/detail','limit':10000,'offset':0,'headers':headers}

print('----------网易云音乐爬虫 by Hisheng v1.0.1--------')
print('请选择操作选项：')
print('1.通过html文件爬取')
print('2.其他')
option = input()
option = int(option)
if option == 1:
	filename = input('请输入文件名：')
	process_num = input('请输入要执行的进程数：')
	process_num = int(process_num)

	music = Music()
	song_lists = music.get_song_lists_by_filename(filename)
	print('开始抓取相关歌曲信息...')
	music.crawl_song_info_by_song_lists(song_lists,params)
	print('相关歌曲信息抓取已结束！')
else:
	print('无相关操作选项！')