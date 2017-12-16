from socket import *
import SocketServer
import ssl
import subporcess
import pipes
import os

def unpack_http_header(header) :
	element_line = header.rstrip('\r\n\r\n').split('\r\n')
	first_method = element_line[0]
	result = dict()
	for one in element_line[1:]:
		key, value = one.split(': ', 1)
		value = value.lstrip()
		result[key] = value
	return first_method, result

class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):
	def receive_http_request(self):
		packet = ''
		while True :
			packet += self.request.recv(1) #from client
			if '\r\n\r\n' in packet:
				break
		return packet

	def receive_http_response_header(self, s):
		packet = ''
		while True :
			packet += s.recv(1)			#from server
			if '\r\n\r\n' in packet:
				break
		return packet


	def forward_body(self, s, n):
		t = ''
		for _ in xrange(n):
            		t += s.recv(1)
		print t
		self.request.send(t)

	def handle(self):
		data = self.receive_http_request()
		request_header = unpack_http_header(data)[1]

		host = request_header['Host']
		port = 443
		if ':' in host:
			host, port = host.split(':', 1)
			port = int(port)

		s = socket(AF_INET, SOCK_STREAM)
		s.connect((host,80))
		self.request.send('HTTP/1.1 200 Connection established\r\nConnection: close\r\n\r\n')

		cert_dir = 'cert-master/' + host + '.pem'
		if not os.path.isfile(cert_dir):
			os.system('cd cert-master;./_make_site.sh ' + host)
		self.request = ssl.wrap_socket(self.request, certfile=cert+dir, server_side=True)


		ssl_data = self.receive_http_request()
		first_line, request_header = unpack_http_header(ssl_data)

		s.send(ssl_data)
		real_header = self.receive_http_response_header(s)
		response_header = unpack_http_header(real_header)[1]

		if response_header.get('Transfer-Encoding', '') == 'chunked':
			self.request.send(real_header)
			while True :
				buf = ''
				while True :
					buf += s.recv(1)
					if'\r\n' in buf:
						break
				self.request.send(buf)
				chunk_length = int(buf, 16)
				self.forward_body(s, chunk_length+2)
				if not chunk_length:
					break
		else :
			self.request.send(real_header)
			self.forward_body(s, int(response_header.get('Content-Length', '0')))

	def finish(self):
		pass

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
	pass

if __name__ == "__main__":
	SocketServer.TCPServer.allow_reuse_address = True
	HOST, PORT = "localhost", 6666
	server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
	server.serve_forever()