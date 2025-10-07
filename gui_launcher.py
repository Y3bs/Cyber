import threading
import time
import socket

import webview

from app import app


def _is_port_open(host: str, port: int) -> bool:
	try:
		with socket.create_connection((host, port), timeout=0.5):
			return True
	except OSError:
		return False


def run_server():
	app.run(debug=False, host='127.0.0.1', port=5000)


def main():
	server_thread = threading.Thread(target=run_server, daemon=True)
	server_thread.start()

	for _ in range(200):
		if _is_port_open('127.0.0.1', 5000):
			break
		time.sleep(0.05)

	webview.create_window('Leader', 'http://127.0.0.1:5000', width=1200, height=800, resizable=True)
	webview.start()


if __name__ == '__main__':
	main()
