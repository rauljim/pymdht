core
====

:mod:`bencode`
--------------
.. automodule:: bencode

:mod:`floodbarrier`
-------------------
.. automodule:: floodbarrier

:mod:`logging_conf`
-------------------
.. automodule:: logging_conf

:mod:`message_tools`
--------------------
.. automodule:: message_tools


:mod:`ptime`
------------
.. automodule:: ptime

:mod:`state`
------------
.. automodule:: state

:mod:`token_manager`
--------------------
.. automodule:: token_manager


:mod:`utils`
------------
.. automodule:: utils


:mod:`identifier`
-----------------
.. automodule:: identifier
   :members:



:mod:`node`
-----------
.. automodule:: node
   :members:

:mod:`message`
--------------
.. automodule:: message
   :members:

:mod:`minitwisted`
------------------
Minitwisted is a very simple, yet important, module. This module controls a
thread used internally in the pymdht package. This thread waits for events (a
new datagram from the network or an scheduled task) and calls the appropriated
callback functions which will handle such events.

There are three different events: (1) heartbeat events, (2) external events,
and (3) networking events. Each event is handled by a different function. All
these functions return the object structure: a tuple containing two elements:
a time-stamp and a list of datagrams.

Heartbeat events are generated frequently. The very first heartbeat is
scheduled to be triggered right after the \textit{ThreadedReactor} object
instantiation. The heartbeat handler is always the same and it is given to the
object. The time-stamp returned by handlers of any event determine when the
next heartbeat event will be triggered.

External events are generated outside the pacemaker thread by calling
\textbf{call\_asap()}. This function requires the handler to be called and its
arguments. The external event will be scheduled to be triggered as possible
(hence the method name). The main purpose of this mechanism is to execute the
function given as handler from the pacemaker thread. ??more here

Networking events are triggered every time a new datagram is received on the
UDP port given in the object constructor. The handler is given a
message.Datagram object containing the UDP data and the address of the sender.

Every handler returns a tuple containing a time-stamp and a list of datagrams
(message.Datagram). ThreadReactor will immediately send the datagrams over the
network and schedule a heartbeat event to be triggered at the time specified
by the time-stamp.

Implementation note. Given the current implementation, heartbeat
events will be triggered shortly after the time specified by the
time-stamp. This delay can be reduced by decreasing 'task\_interval', which
regulates the maximum time the thread sleeps between events. The same delay
applies to external events. Networking events, however, are asynchronous and
will be triggered immediately.

.. automodule:: minitwisted
   :members:

:mod:`controller`
-----------------
.. automodule:: controller
   :members:

:mod:`tracker`
--------------
.. automodule:: tracker
   :members:

:mod:`querier`
--------------
.. automodule:: querier
   :members:

:mod:`routing_table`
--------------------
.. automodule:: routing_table
   :members:


