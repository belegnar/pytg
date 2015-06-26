# -*- coding: utf-8 -*-

__author__ = 'luckydonald'

import logging
logger = logging.getLogger(__name__)
import threading
from collections import deque
from types import GeneratorType

from ..utils import coroutine

class PublicInterface(object):
	def __init__(self):
		super(PublicInterface, self).__init__()
		self.message_constructor = None
		self._do_quit = False
		self._queue = deque()
		self._new_messages = threading.Semaphore(0)
		self._queue_access = threading.Lock()
		self._receiver_thread = None
		self._block_generator_routine = True  # so the cli-python disable that. It needs active polling.

	def _add_message(self, raw_event):
		"""
		Appends a message to the message queue.

		:type text: builtins.str
		:return:
		"""
		json_dict = {}
		logger.debug("Received Message: \"{str}\"".format(str=raw_event))
		with self._queue_access:
			self._queue.append(raw_event) # change me!
			self._new_messages.release()

	def start(self):
		"""
		Starts the receiver.
		When started, messages will be queued.
		:return:
		"""
		self._receiver_thread = threading.Thread(name="Receiver (pytg)", target=self._receiver, args=())
		self._receiver_thread.daemon = True  # exit if script reaches end.
		self._receiver_thread.start()

	def stop(self):
		"""
		Shuts down the receivers.
		No more messages will be queued.
		"""
		self._do_quit = True
		self._receiver_thread.join()

	def _receiver(self):
		"""
		Function which will be started in a new thread to queue messages.
		This function should enqueue all new messages with self._add_message(obj)
		"""

	def queued_messages(self):
		"""
		Informs how many messages are still in the queue, waiting to be processed.

		:return: integer, the messages currently in queue.
		:rtype: int
		"""
		with self._queue_access:
			return len(self._queue)

	@coroutine
	def for_each_event(self, function):
		if not isinstance(function, GeneratorType):
			raise TypeError('Target must be GeneratorType')
		try:
			while not self._do_quit:
				self._routine(function)
		except GeneratorExit:
			pass
		except KeyboardInterrupt:
			raise StopIteration

	def _routine(self, function):
		if self._do_quit:
			raise GeneratorExit("do_quit=True")
		if not self._new_messages.acquire(blocking=self._block_generator_routine): # waits until at least 1 message is in the queue.
			return
		with self._queue_access:
			raw_event = self._queue.popleft()  # pop oldest item
			msg = self.message_constructor.new_event(raw_event)
			logger.debug('Messages waiting in queue: %d', len(self._queue))
		function.send(msg)



class MessageConstructorSuperclass(object):
	def new_event(self, raw_event):
		raise NotImplementedError("new_event() is not implemented")