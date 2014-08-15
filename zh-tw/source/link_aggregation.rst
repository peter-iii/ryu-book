.. _ch_link_aggregation:

Link Aggregation
========================

本章會說明，Ryu 使用的 link aggregation 功能的實作方法。



Link Aggregation
------------------------

link aggregation 是由 IEEE802.1AX-2008 所制定的，多條實體線路合併為一個邏輯線路。
透過本功能可以讓網路中特定的裝置間通訊速度提升，同時確保備援能力提升容錯的功能。



.. only:: latex

  .. image:: images/link_aggregation/fig1.eps
     :scale: 80%
     :align: center

.. only:: epub

  .. image:: images/link_aggregation/fig1.png
     :align: center

.. only:: not latex and not epub

  .. image:: images/link_aggregation/fig1.png
     :scale: 40%
     :align: center

在使用 link aggregation 功能之前，個別的網路裝置上哪一個界面歸屬于哪一個群組都必須先設定完成。

起始 link aggregation 功能的方法是將個別的網路裝置設置完成，此為靜態方法。
另外也可以使用 LACP (Link Aggregation Control Protocol) 通訊協定，此為動態方法。

採用動態方法的時候，每一個網路裝置所相對應的界面會定期的進行 LACP data unit 交換以確認彼此之間的通訊狀況。
當 LACP data unit 的交換無法完成，代表網路已經出現故障，使用該網路的裝置出現通訊中斷，
此時封包的傳送僅能使用殘存的界面和線路完成。

在採用了動態的方法情況下，每一個網路裝置所對應的界面會定期的交換 LACP data unit，以確認相互間通訊的狀態。
當 LACP data unit 無法傳送或接收的時候，則代表裝置間的連接出現了問題，網路處於無法使用的狀態。
此時可以交換封包的僅剩下那些尚未中斷網路的殘存線路。
這樣的做法有個優點，即當有個轉送裝置存在于網路之中，例如 meida converter，就可以知道當該裝置的另外一端也斷線時可以被偵測到。本章將會說明使用 LACP 進行動態的 link aggregation 設置。



執行 Ryu 應用程式
-------------------------

原始碼的解說將放到後面，首先式 Ryu 的 link aggregation 應用程式的執行。

simple_switch_lacp.py 為 OpenFlow 1.0 專用的應用程式並存在于 Ryu 的原始碼中。
在這邊我們要建立新的 OpenFlow 1.3 版本，即 simple_switch_lacp_13.py。
此應用程式為「 :ref:`ch_switching_hub` 」中交換器新增 link aggregation 功能。

``
原始碼名稱： ``simple_switch_lacp_13.py``

.. rst-class:: sourcecode

.. literalinclude:: sources/simple_switch_lacp_13.py


實驗環境的建置
^^^^^^^^^^^^^^

讓我們來看一下 OpenFlow 交換器和 Linux host 之間的 link aggregation 。

為了使用 VM 映像檔，詳細的環境設定和登入方法等請參考 「 :ref:`ch_switching_hub` 」。

首先使用 Mininet 製作出如下一般的網路拓璞。

.. only:: latex

   .. image:: images/link_aggregation/fig2.eps
      :scale: 80%
      :align: center

.. only:: epub

   .. image:: images/link_aggregation/fig2.png
      :align: center

.. only:: not latex and not epub

   .. image:: images/link_aggregation/fig2.png
      :scale: 40%
      :align: center

使用 script 來呼叫 Mininet 的 API 進而完成網路拓璞的建構。


原始碼名稱： ``link_aggregation.py``

.. rst-class:: sourcecode

.. literalinclude:: sources/link_aggregation.py

執行該 script 後會形成 host 1 和交換器 s1 之間有兩條連線的拓璞結構。這時可以使用 net 命令來進行確認。

.. rst-class:: console

::

    ryu@ryu-vm:~$ sudo ./link_aggregation.py
    Unable to contact the remote controller at 127.0.0.1:6633
    mininet> net
    c0
    s1 lo:  s1-eth1:h1-eth0 s1-eth2:h1-eth1 s1-eth3:h2-eth0 s1-eth4:h3-eth0 s1-eth5:h4-eth0
    h1 h1-eth0:s1-eth1 h1-eth1:s1-eth2
    h2 h2-eth0:s1-eth3
    h3 h3-eth0:s1-eth4
    h4 h4-eth0:s1-eth5
    mininet>


host h1 的 link aggregation 設定
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

在這之前 host h1 的 Linux 作業系統中必須先行設定。

請輸入本節的命令在 host h1 的 xterm 終端機之中。

首先，載入 drive module 以完成 link aggregation 。
在 Linux 之中，link aggregation 功能是由 bonding drive 所處理。
預先建立 drive 的設定檔 /etc/modprobe.d/bonding.conf 以完成該功能。


檔案名稱: ``/etc/modprobe.d/bonding.conf``

.. rst-class:: sourcecode

::

    alias bond0 bonding
    options bonding mode=4

Node: h1:

.. rst-class:: console

::

    root@ryu-vm:~# modprobe bonding

mode=4 是 LACP 中代表使用 dynamic link aggregation。
由於是預設值的關係，這邊可以省略。而 LACP data unit 的交換間隔為 SLOW (30秒)，並且排序的方式是使用目標 MAC address 來進行。

接著，建立一個名為 bond0 的邏輯界面。然後設 bond0 的 MAC address。

Node: h1:

.. rst-class:: console

::

    root@ryu-vm:~# ip link add bond0 type bond
    root@ryu-vm:~# ip link set bond0 address 02:01:02:03:04:08

把 h1-eth0 和 h1-eth1 的實體網路界面加到建立好的邏輯界面群組中。此時，先將實體界面設定為 down，然後亂數決定該實體界面較為簡單的 MAC address 並更新。



Node: h1:

.. rst-class:: console

::

    root@ryu-vm:~# ip link set h1-eth0 down
    root@ryu-vm:~# ip link set h1-eth0 address 00:00:00:00:00:11
    root@ryu-vm:~# ip link set h1-eth0 master bond0
    root@ryu-vm:~# ip link set h1-eth1 down
    root@ryu-vm:~# ip link set h1-eth1 address 00:00:00:00:00:12
    root@ryu-vm:~# ip link set h1-eth1 master bond0

指定邏輯界面的 IP address。
這邊是指定為 10.0.0.1。由於 h1-eth0 的 IP address 已經被指定所以我們刪除它。



Node: h1:

.. rst-class:: console

::

    root@ryu-vm:~# ip addr add 10.0.0.1/8 dev bond0
    root@ryu-vm:~# ip addr del 10.0.0.1/8 dev h1-eth0

最後，設定邏輯界面為 UP。



Node: h1:

.. rst-class:: console

::

    root@ryu-vm:~# ip link set bond0 up

接著確認每一個界面的狀態。



Node: h1:

.. rst-class:: console

::

    root@ryu-vm:~# ifconfig
    bond0     Link encap:Ethernet  HWaddr 02:01:02:03:04:08
              inet addr:10.0.0.1  Bcast:0.0.0.0  Mask:255.0.0.0
              UP BROADCAST RUNNING MASTER MULTICAST  MTU:1500  Metric:1
              RX packets:0 errors:0 dropped:0 overruns:0 frame:0
              TX packets:10 errors:0 dropped:0 overruns:0 carrier:0
              collisions:0 txqueuelen:0
              RX bytes:0 (0.0 B)  TX bytes:1240 (1.2 KB)

    h1-eth0   Link encap:Ethernet  HWaddr 02:01:02:03:04:08
              UP BROADCAST RUNNING SLAVE MULTICAST  MTU:1500  Metric:1
              RX packets:0 errors:0 dropped:0 overruns:0 frame:0
              TX packets:5 errors:0 dropped:0 overruns:0 carrier:0
              collisions:0 txqueuelen:1000
              RX bytes:0 (0.0 B)  TX bytes:620 (620.0 B)

    h1-eth1   Link encap:Ethernet  HWaddr 02:01:02:03:04:08
              UP BROADCAST RUNNING SLAVE MULTICAST  MTU:1500  Metric:1
              RX packets:0 errors:0 dropped:0 overruns:0 frame:0
              TX packets:5 errors:0 dropped:0 overruns:0 carrier:0
              collisions:0 txqueuelen:1000
              RX bytes:0 (0.0 B)  TX bytes:620 (620.0 B)

    lo        Link encap:Local Loopback
              inet addr:127.0.0.1  Mask:255.0.0.0
              UP LOOPBACK RUNNING  MTU:16436  Metric:1
              RX packets:0 errors:0 dropped:0 overruns:0 frame:0
              TX packets:0 errors:0 dropped:0 overruns:0 carrier:0
              collisions:0 txqueuelen:0
              RX bytes:0 (0.0 B)  TX bytes:0 (0.0 B)

邏輯界面 bond0 為 MASTER，實體界面 h1-eth0 和 h1-eth1 為 SLAVE。
而且，你可以看到 bond0、h1-eth0 和 h1-eth1 的 MAC address 全部都是相同的。

確認 bonding driver 的狀態。

Node: h1:

.. rst-class:: console

::

    root@ryu-vm:~# cat /proc/net/bonding/bond0
    Ethernet Channel Bonding Driver: v3.7.1 (April 27, 2011)

    Bonding Mode: IEEE 802.3ad Dynamic link aggregation
    Transmit Hash Policy: layer2 (0)
    MII Status: up
    MII Polling Interval (ms): 100
    Up Delay (ms): 0
    Down Delay (ms): 0

    802.3ad info
    LACP rate: slow
    Min links: 0
    Aggregator selection policy (ad_select): stable
    Active Aggregator Info:
            Aggregator ID: 1
            Number of ports: 1
            Actor Key: 33
            Partner Key: 1
            Partner Mac Address: 00:00:00:00:00:00

    Slave Interface: h1-eth0
    MII Status: up
    Speed: 10000 Mbps
    Duplex: full
    Link Failure Count: 0
    Permanent HW addr: 00:00:00:00:00:11
    Aggregator ID: 1
    Slave queue ID: 0

    Slave Interface: h1-eth1
    MII Status: up
    Speed: 10000 Mbps
    Duplex: full
    Link Failure Count: 0
    Permanent HW addr: 00:00:00:00:00:12
    Aggregator ID: 2
    Slave queue ID: 0

確認 LACP data unit 的交換間隔(LACP rate: slow) 和排序邏輯的設定(Transmit Hash Policy: layer2 (0))。
必且確認實體界面 h1-eth0 和 h1-eth1 的 MAC addresss。

以上為 host h1 的事前準備。


設定 OpenFlow 版本
^^^^^^^^^^^^^^^^^^^^^^^^

交換器 s1 的 OpenFlow 版本設定為 1.3。請在交換器s1的 xterm 終端機上輸入下面的指令。



Node: s1:

.. rst-class:: console

::

    root@ryu-vm:~# ovs-vsctl set Bridge s1 protocols=OpenFlow13


執行交換器
^^^^^^^^^^^^^^^^^^^^^^

準備完成。接著開始執行 Ryu 應用程式。

在視窗標題為 「Node: c0 (root)」 的 xterm 終端機中執行下列的命令。



Node: c0:

.. rst-class:: console

::

    ryu@ryu-vm:~$ ryu-manager ./simple_switch_lacp_13.py
    loading app ./simple_switch_lacp_13.py
    loading app ryu.controller.ofp_handler
    creating context lacplib
    instantiating app ./simple_switch_lacp_13.py
    instantiating app ryu.controller.ofp_handler
    ...

host h1 會在每30秒發送一次 LACP data unit。啟動之後，交換器馬上就會收到 host h1 發送的 LACP data unit，並輸出記錄在 log 之中。　



Node: c0:

.. rst-class:: console

::

    ...
    [LACP][INFO] SW=0000000000000001 PORT=1 LACP received.
    [LACP][INFO] SW=0000000000000001 PORT=1 the slave i/f has just been up.
    [LACP][INFO] SW=0000000000000001 PORT=1 the timeout time has changed.
    [LACP][INFO] SW=0000000000000001 PORT=1 LACP sent.
    slave state changed port: 1 enabled: True
    [LACP][INFO] SW=0000000000000001 PORT=2 LACP received.
    [LACP][INFO] SW=0000000000000001 PORT=2 the slave i/f has just been up.
    [LACP][INFO] SW=0000000000000001 PORT=2 the timeout time has changed.
    [LACP][INFO] SW=0000000000000001 PORT=2 LACP sent.
    slave state changed port: 2 enabled: True
    ...

下面說明 log 的內容。

* LACP received.

    接受到 LACP data unit。

* the slave i/f has just been up.

    原本停用的連接埠轉換成啟用狀態。

* the timeout time has changed.

    LACP data unit 的逾時時間變更(本例子中原始狀態為0秒，變更為 LONG_TIMEOUT_TIME 的90秒)

* LACP sent.

    回覆用的 LACP data unit 傳送完畢

* slave state changed ...

    應用程式接收到 LACP 函式庫中 ``EventSlaveStateChanged`` 事件訊息(事件的詳細內容稍後說明)。

交換器對於每一次從 host h1 收到的 LACP data unit 傳送回覆用的 LACP data unit 。



Node: c0:

.. rst-class:: console

::

    ...
    [LACP][INFO] SW=0000000000000001 PORT=1 LACP received.
    [LACP][INFO] SW=0000000000000001 PORT=1 LACP sent.
    [LACP][INFO] SW=0000000000000001 PORT=2 LACP received.
    [LACP][INFO] SW=0000000000000001 PORT=2 LACP sent.
    ...

確認 Flow Entry 。

Node: s1:

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x0, duration=14.565s, table=0, n_packets=1, n_bytes=124, idle_timeout=90, send_flow_rem priority=65535,in_port=2,dl_src=00:00:00:00:00:12,dl_type=0x8809 actions=CONTROLLER:65509
     cookie=0x0, duration=14.562s, table=0, n_packets=1, n_bytes=124, idle_timeout=90, send_flow_rem priority=65535,in_port=1,dl_src=00:00:00:00:00:11,dl_type=0x8809 actions=CONTROLLER:65509
     cookie=0x0, duration=24.821s, table=0, n_packets=2, n_bytes=248, priority=0 actions=CONTROLLER:65535

在交換器中

* 接收到從 h1 的 h1-eth1 (接收埠為 s1-eth2 且目的 MAC address 為 00:00:00:00:00:12) 傳送 LACP data unit (ethertype 0x8809)時就發送 Packet-In 訊息。

* 接收到從 h1 的 h1-eth0 (接收埠為 s1-eth1 且目的 MAC address 為 00:00:00:00:00:11) 傳送 LACP data unit (ethertype 0x8809)時就發送 Packet-In 訊息。

* 跟「 :ref:`ch_switching_hub` 」一樣的 Table-miss Flow Entry

以上3個 Flow Entry 被新增到交換器之中。


確認 link aggregation 功能
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

改善傳送速度
""""""""""""""

首先是確認 link aggregation 的傳送速度。
讓我們來看看使用不同的線路來進行通訊的狀況。

首先，從 host h2 向 host h1 發送 ping 封包。



Node: h2:

.. rst-class:: console

::

    root@ryu-vm:~# ping 10.0.0.1
    PING 10.0.0.1 (10.0.0.1) 56(84) bytes of data.
    64 bytes from 10.0.0.1: icmp_req=1 ttl=64 time=93.0 ms
    64 bytes from 10.0.0.1: icmp_req=2 ttl=64 time=0.266 ms
    64 bytes from 10.0.0.1: icmp_req=3 ttl=64 time=0.075 ms
    64 bytes from 10.0.0.1: icmp_req=4 ttl=64 time=0.065 ms
    ...

當 ping 訊息持續發送的同時，確認交換器 s1 的 Flow Entry 。



Node: s1:

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x0, duration=22.05s, table=0, n_packets=1, n_bytes=124, idle_timeout=90, send_flow_rem priority=65535,in_port=2,dl_src=00:00:00:00:00:12,dl_type=0x8809 actions=CONTROLLER:65509
     cookie=0x0, duration=22.046s, table=0, n_packets=1, n_bytes=124, idle_timeout=90, send_flow_rem priority=65535,in_port=1,dl_src=00:00:00:00:00:11,dl_type=0x8809 actions=CONTROLLER:65509
     cookie=0x0, duration=33.046s, table=0, n_packets=6, n_bytes=472, priority=0 actions=CONTROLLER:65535
     cookie=0x0, duration=3.259s, table=0, n_packets=3, n_bytes=294, priority=1,in_port=3,dl_dst=02:01:02:03:04:08 actions=output:1
     cookie=0x0, duration=3.262s, table=0, n_packets=4, n_bytes=392, priority=1,in_port=1,dl_dst=00:00:00:00:00:22 actions=output:3

在確認過後就會新增下面兩個 Flow Entry。
第四和第五 Flow Entry 會有較小的 duration 的值。

分別是

* 若是收到從第3連接埠(s1-eth3、也就是連接到 h2 的界面)向 h1 的 bond0 發送的封包就轉送到第1連接埠(s1-eth1)。

* 若是收到來自第1連接埠(s1-eth1)向第2連接埠發送的封包，就從第3連接埠(s1-eth3)轉送出去。

接著你可以看到 h2 和 h1 之間的通訊是使用 s1-eth1 來完成。

接著，從 host h3 向 host h1 發送 ping 訊息。



Node: h3:

.. rst-class:: console

::

    root@ryu-vm:~# ping 10.0.0.1
    PING 10.0.0.1 (10.0.0.1) 56(84) bytes of data.
    64 bytes from 10.0.0.1: icmp_req=1 ttl=64 time=91.2 ms
    64 bytes from 10.0.0.1: icmp_req=2 ttl=64 time=0.256 ms
    64 bytes from 10.0.0.1: icmp_req=3 ttl=64 time=0.057 ms
    64 bytes from 10.0.0.1: icmp_req=4 ttl=64 time=0.073 ms
    ...

在 ping 持續發送時，確認交換器 s1 的 Flow Entry。


Node: s1:

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x0, duration=99.765s, table=0, n_packets=4, n_bytes=496, idle_timeout=90, send_flow_rem priority=65535,in_port=2,dl_src=00:00:00:00:00:12,dl_type=0x8809 actions=CONTROLLER:65509
     cookie=0x0, duration=99.761s, table=0, n_packets=4, n_bytes=496, idle_timeout=90, send_flow_rem priority=65535,in_port=1,dl_src=00:00:00:00:00:11,dl_type=0x8809 actions=CONTROLLER:65509
     cookie=0x0, duration=110.761s, table=0, n_packets=10, n_bytes=696, priority=0 actions=CONTROLLER:65535
     cookie=0x0, duration=80.974s, table=0, n_packets=82, n_bytes=7924, priority=1,in_port=3,dl_dst=02:01:02:03:04:08 actions=output:1
     cookie=0x0, duration=2.677s, table=0, n_packets=2, n_bytes=196, priority=1,in_port=2,dl_dst=00:00:00:00:00:23 actions=output:4
     cookie=0x0, duration=2.675s, table=0, n_packets=1, n_bytes=98, priority=1,in_port=4,dl_dst=02:01:02:03:04:08 actions=output:2
     cookie=0x0, duration=80.977s, table=0, n_packets=83, n_bytes=8022, priority=1,in_port=1,dl_dst=00:00:00:00:00:22 actions=output:3

在剛才確認的時候，2個 Flow Entry 已經新增。duration值較小的 Flow Entry 為第5和第6個 Entry。

分別是

* 收到從第2連接埠(s1-eth2)向 h3 發送的封包時就從第4連接埠(s1-eth4)轉送出去

* 收到從第4連接埠(s1-eth4，也就是連接到 h3 的界面)向 h1 的 bond0 發送的封包時就從第2連接埠(s1-eth2)轉送出去

這樣可以看出 h3 和 h1 之間的通訊是使用 s1-eth2 在進行轉送。

當然 host 4 向 host h1 發送的 ping 指令就可以正常動作。
到此為止同樣的新 Flow Entry 被新增，h4 和 h1 之間的通訊就使用 s1-eth1 來傳送。


============ ============
目的 host    使用連接埠
============ ============
h2           1
h3           2
h4           1
============ ============

.. only:: latex

   .. image:: images/link_aggregation/fig3.eps
      :scale: 80%
      :align: center

.. only:: epub

   .. image:: images/link_aggregation/fig3.png
      :align: center

.. only:: not latex and not epub

   .. image:: images/link_aggregation/fig3.png
      :scale: 40%
      :align: center

透過以上的動作，可以確認多條線路的通訊狀態。



提升容錯能力
""""""""""""""

接下來，我們要提升 link aggregation 的容錯能力。
現在的狀況是 h2、h4 和 h1 之間的通訊是使用 s1-eth2 連接埠， h3 和 h1 的通訊是使用 s1-eth1 連接埠。

在這邊，我們把 s1-eth1 從所屬的 s1-eth0 link aggregation 群組中分離出來。

Node: h1:

.. rst-class:: console

::

    root@ryu-vm:~# ip link set h1-eth0 nomaster

當 h1-eth0 停用時，host h3 向 host h1 的 ping 是無法連通的。
在停止通訊的狀態下經過了 90 秒之後，下面的 log 上會出現 controller 的動作訊息。

Node: c0:

.. rst-class:: console

::

    ...
    [LACP][INFO] SW=0000000000000001 PORT=1 LACP received.
    [LACP][INFO] SW=0000000000000001 PORT=1 LACP sent.
    [LACP][INFO] SW=0000000000000001 PORT=2 LACP received.
    [LACP][INFO] SW=0000000000000001 PORT=2 LACP sent.
    [LACP][INFO] SW=0000000000000001 PORT=2 LACP received.
    [LACP][INFO] SW=0000000000000001 PORT=2 LACP sent.
    [LACP][INFO] SW=0000000000000001 PORT=2 LACP received.
    [LACP][INFO] SW=0000000000000001 PORT=2 LACP sent.
    [LACP][INFO] SW=0000000000000001 PORT=1 LACP exchange timeout has occurred.
    slave state changed port: 1 enabled: False
    ...

「LACP exchange timeout has occurred.」表示停止通訊已經逾時，
曾經學習過的 MAC address 和轉送封包用的 Flow Entry 全部被刪除，
回到如同剛開機時的狀態。

當新的通訊發生時，新的 MAC address 將會被學習，已存在的線路連結 Flow Entry 將會再次被新增。

host h3 和 host h1 之間的新 Flow Entry 會被新增。

Node: s1:

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x0, duration=364.265s, table=0, n_packets=13, n_bytes=1612, idle_timeout=90, send_flow_rem priority=65535,in_port=2,dl_src=00:00:00:00:00:12,dl_type=0x8809 actions=CONTROLLER:65509
     cookie=0x0, duration=374.521s, table=0, n_packets=25, n_bytes=1830, priority=0 actions=CONTROLLER:65535
     cookie=0x0, duration=5.738s, table=0, n_packets=5, n_bytes=490, priority=1,in_port=3,dl_dst=02:01:02:03:04:08 actions=output:2
     cookie=0x0, duration=6.279s, table=0, n_packets=5, n_bytes=490, priority=1,in_port=2,dl_dst=00:00:00:00:00:23 actions=output:5
     cookie=0x0, duration=6.281s, table=0, n_packets=5, n_bytes=490, priority=1,in_port=5,dl_dst=02:01:02:03:04:08 actions=output:2
     cookie=0x0, duration=5.506s, table=0, n_packets=5, n_bytes=434, priority=1,in_port=4,dl_dst=02:01:02:03:04:08 actions=output:2
     cookie=0x0, duration=5.736s, table=0, n_packets=5, n_bytes=490, priority=1,in_port=2,dl_dst=00:00:00:00:00:21 actions=output:3
     cookie=0x0, duration=6.504s, table=0, n_packets=6, n_bytes=532, priority=1,in_port=2,dl_dst=00:00:00:00:00:22 actions=output:4

host h3 的 ping 恢復正常。

Node: h3:

.. rst-class:: console

::


    ...
    64 bytes from 10.0.0.1: icmp_req=144 ttl=64 time=0.193 ms
    64 bytes from 10.0.0.1: icmp_req=145 ttl=64 time=0.081 ms
    64 bytes from 10.0.0.1: icmp_req=146 ttl=64 time=0.095 ms
    64 bytes from 10.0.0.1: icmp_req=237 ttl=64 time=44.1 ms
    64 bytes from 10.0.0.1: icmp_req=238 ttl=64 time=2.52 ms
    64 bytes from 10.0.0.1: icmp_req=239 ttl=64 time=0.371 ms
    64 bytes from 10.0.0.1: icmp_req=240 ttl=64 time=0.103 ms
    64 bytes from 10.0.0.1: icmp_req=241 ttl=64 time=0.067 ms
    ...

經過以上的說明，當一部份的 link 發生故障的時候，我們可以確認到其他的 link 會自動的恢復以進行通訊。



實作 Ryu 的 link aggregation 功能
-------------------------------------------


讓我們來看看如何利用 OpenFlow 實作 Link aggregation 功能。

使用 LCAP 的 link aggregation 的行為會像是
「當 LACP data unit 傳遞正常時，則表示所使用的實體界面為啟用狀態」
「反之，當 LACP data unit 傳遞不正常時，則表示所使用的實體界面為停用或無效狀態」
實體界面無效的意思是，該界面並無相關聯的 Flow Entry 存在。
因此透過下面的步驟：

* 實作接收並回覆 LACP data unit
* 在一個固定的時間區間中沒有收到 LACP data unit 時，則刪除該實體界面所使用到及之後的 Flow Entry
* 已經停用的實體界面若是收到了 LACP data unit 封包，則啟用該界面。
* LACP data unit 以外的封包則比照 「 :ref:`ch_switching_hub` 」進行學習及轉送。

經過以上的處理及安裝後，Link aggregation 基本的動作已經完成。
LACP 相關的部分和不相關的部分已經可以被明顯的區隔出來，對於不相關的部分請參考「 :ref:`ch_switching_hub` 」以進行交換器的擴充實作。

在接收到 LACP data unit 時給予回覆這件事情無法單純使用 Flow Entry 來實現。
因此，Packet-In 訊息被用來支援處理 OpenFlow controller 方面的溝通。


.. NOTE::

    用來交換 LACP data unit 的實體界面被分為兩種角色，主動(ACTIVE)與被動(PASSIVE)形態。
    主動是在固定的時間會發送 LACP data unit ，以確認線路的狀態。
    被動則是在收到主動狀態發送過來的 LACP data unit 時予以回覆，以確認線路的狀態。

    在 Ryu 中的 link aggregation 應用程式是使用被動模式(PASSIVE mode)來實作。


若是在特定的時間內沒有收到 LACP data unit ，則該實體界面視為無效。
會這樣是因為先前 LACP data unit 促使 Packet-In 並進行 Flow Entry 新增時設定了 idle_timeout。
當時間超過該設定值時，發送 FlowRemoved 訊息通知 controller。Controller 則讓該界面無效。

已經處於無效狀態的界面收到 LACP data unit 的時候的處理為：
接收到 LACP data unit 的時候 Packet-In 訊息的封包會作為該界面的有效或無效的判斷標準，並進行必要的變更。

若實體界面為無效時，OpenFlow controller 最簡單的處理為「刪除該界面所使用到的 Flow Entry」，但是這樣的條件其實是不充分的。

例如：有一個邏輯界面是由三個實體界面群組化之後所產生，其排序為「依照啟用界面的數量排序 MAC address」。

====================  ====================  =================
界面1                  界面2                 界面3
====================  ====================  =================
殘存 MAC address:0     殘存 MAC address:1     殘存 MAC address:2
====================  ====================  =================

然後，每一個實體界面所使用的 Flow Entry 分別新增如下。

=======================  =======================  ====================
界面1                    界面2                     界面3
=======================  =======================  ====================
宛先:00:00:00:00:00:00   宛先:00:00:00:00:00:01   宛先:00:00:00:00:00:02
宛先:00:00:00:00:00:03   宛先:00:00:00:00:00:04   宛先:00:00:00:00:00:05
宛先:00:00:00:00:00:06   宛先:00:00:00:00:00:07   宛先:00:00:00:00:00:08
=======================  =======================  ====================

因此，如果在界面1為無效的狀態下，「在有效的界面中以殘存的 MAC addresss 數量為準」作為排序的標準，排序結果如下。

====================  ====================  =================
界面1                 界面2                  界面3
====================  ====================  =================
停用                  殘存 MAC addresss:0    殘存 MAC address:1
====================  ====================  =================

=======================  =======================  ====================
界面1                    界面2                     界面3
=======================  =======================  ====================
\                        目的:00:00:00:00:00:00   目的:00:00:00:00:00:01
\                        目的:00:00:00:00:00:02   目的:00:00:00:00:00:03
\                        目的:00:00:00:00:00:04   目的:00:00:00:00:00:05
\                        目的:00:00:00:00:00:06   目的:00:00:00:00:00:07
\                        目的:00:00:00:00:00:08
=======================  =======================  ====================

インターフェース1を使用していたフローエントリだけではなく、インターフェース2や
インターフェース3のフローエントリも書き換える必要があることがわかります。これ
は物理インターフェースが無効になったときだけでなく、有効になったときも同様で
す。

従って、ある物理インターフェースの有効/無効状態が変更された場合の処理は、当該
物理インターフェースが所属する論理インターフェースに含まれるすべての物理イン
ターフェースを使用するフローエントリを削除する、としています。

.. NOTE::

    振り分けロジックについては仕様で定められておらず、各機器の実装に委ねられ
    ています。Ryuのリンク・アグリゲーション・アプリケーションでは独自の振り
    分け処理を行わず、対向装置によって振り分けられた経路を使用していま
    す。

ここでは、次のような機能を実装します。

**LACPライブラリ**

* LACPデータユニットを受信したら応答を作成して送信する
* LACPデータユニットの受信が途絶えたら、対応する物理インターフェースを無効とみなし、
  スイッチングハブに通知する
* LACPデータユニットの受信が再開されたら、対応する物理
  インターフェースを有効とみなし、スイッチングハブに通知する

**スイッチングハブ**

* LACPライブラリからの通知を受け、初期化が必要なフローエントリを削除する
* LACPデータユニット以外のパケットは従来どおり学習・転送する


LACPライブラリおよびスイッチングハブのソースコードは、Ryuのソースツリーにあ
ります。

    ryu/lib/lacplib.py

    ryu/app/simple_switch_lacp.py

.. NOTE::

    simple_switch_lacp.pyはOpenFlow 1.0専用のアプリケーション
    であるため、本章では「 `Ryuアプリケーションの実行`_ 」に示した
    OpenFlow 1.3に対応したsimple_switch_lacp_13.pyを元にアプリケーションの
    詳細を説明します。


LACPライブラリの実装
^^^^^^^^^^^^^^^^^^^^

以降の節で、前述の機能がLACPライブラリにおいてどのように実装されてい
るかを見ていきます。なお、引用されているソースは抜粋です。全体像については実
際のソースをご参照ください。


論理インターフェースの作成
""""""""""""""""""""""""""

リンク・アグリゲーション機能を使用するには、どのネットワーク
機器においてどのインターフェースをどのグループとして束ねるのかという設定を事
前に行っておく必要があります。LACPライブラリでは、以下のメソッドでこの設定を
行います。

.. rst-class:: sourcecode

::

    def add(self, dpid, ports):
        # ...
        assert isinstance(ports, list)
        assert 2 <= len(ports)
        ifs = {}
        for port in ports:
            ifs[port] = {'enabled': False, 'timeout': 0}
        bond = {}
        bond[dpid] = ifs
        self._bonds.append(bond)

引数の内容は以下のとおりです。

dpid

    OpenFlowスイッチのデータパスIDを指定します。

ports

    グループ化したいポート番号のリストを指定します。

このメソッドを呼び出すことにより、LACPライブラリは指定されたデータパスIDの
OpenFlowスイッチの指定されたポートをひとつのグループとみなします。
複数のグループを作成したい場合は繰り返しadd()メソッドを呼び出し
ます。なお、論理インターフェースに割り当てられるMACアドレスは、OpenFlow
スイッチの持つLOCALポートと同じものが自動的に使用されます。

.. TIP::

    OpenFlowスイッチの中には、スイッチ自身の機能としてリンク・アグリゲー
    ション機能を提供しているものもあります（Open vSwitchなど）。ここではそ
    うしたスイッチ独自の機能は使用せず、OpenFlowコントローラによる制御に
    よってリンク・アグリゲーション機能を実現します。


Packet-In処理
"""""""""""""

「 :ref:`ch_switching_hub` 」は、宛先のMACアドレスが未学
習の場合、受信したパケットをフラッディングします。LACPデータユニットは隣接す
るネットワーク機器間でのみ交換されるべきもので、他の機器に転送してしまうとリ
ンク・アグリゲーション機能が正しく動作しません。そこで、「Packet-Inで受信し
たパケットがLACPデータユニットであれば横取りし、LACPデータユニット
以外のパケットであればスイッチングハブの動作に委ねる」という処理を行い、
スイッチングハブにはLACPデータユニットを見せないようにします。

.. rst-class:: sourcecode

::

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, evt):
        """PacketIn event handler. when the received packet was LACP,
        proceed it. otherwise, send a event."""
        req_pkt = packet.Packet(evt.msg.data)
        if slow.lacp in req_pkt:
            (req_lacp, ) = req_pkt.get_protocols(slow.lacp)
            (req_eth, ) = req_pkt.get_protocols(ethernet.ethernet)
            self._do_lacp(req_lacp, req_eth.src, evt.msg)
        else:
            self.send_event_to_observers(EventPacketIn(evt.msg))

イベントハンドラ自体は「 :ref:`ch_switching_hub` 」と同様です。受信したメッ
セージにLACPデータユニットが含まれているかどうかで処理を分岐させています。

LACPデータユニットが含まれていた場合はLACPライブラリのLACPデータユニット受
信処理を行います。LACPデータユニットが含まれていなかった場合、
send_event_to_observers()というメソッドを呼んでいます。これは
ryu.base.app_manager.RyuAppクラスで定義されている、イベントを送信するため
のメソッドです。

「 :ref:`ch_switching_hub` 」ではRyuで定義されたOpenFlowメッセージ受信イ
ベントについて触れましたが、ユーザが独自にイベントを定義することもできます。
上記ソースで送信している ``EventPacketIn`` というイベントは、LACPライブラ
リ内で作成したユーザ定義イベントです。

.. rst-class:: sourcecode

::

    class EventPacketIn(event.EventBase):
        """a PacketIn event class using except LACP."""
        def __init__(self, msg):
            """initialization."""
            super(EventPacketIn, self).__init__()
            self.msg = msg

ユーザ定義イベントは、ryu.controller.event.EventBaseクラスを継承して作成
します。イベントクラスに内包するデータに制限はありません。 ``EventPacketIn``
クラスでは、Packet-Inメッセージで受信したryu.ofproto.OFPPacketInインスタン
スをそのまま使用しています。

ユーザ定義イベントの受信方法については後述します。


ポートの有効/無効状態変更に伴う処理
"""""""""""""""""""""""""""""""""""

LACPライブラリのLACPデータユニット受信処理は、以下の処理からなっています。

1. LACPデータユニットを受信したポートが無効状態であれば有効状態に変更
   し、状態が変更したことをイベントで通知します。
2. 無通信タイムアウトの待機時間が変更された場合、LACPデータユニット受信時に
   Packet-Inを送信するフローエントリを再登録します。
3. 受信したLACPデータユニットに対する応答を作成し、送信します。

2.の処理については後述の
「 `LACPデータユニットをPacket-Inさせるフローエントリの登録`_ 」
で、3.の処理については後述の
「 `LACPデータユニットの送受信処理`_ 」
で、それぞれ説明します。ここでは1.の処理について説明します。

.. rst-class:: sourcecode

::

    def _do_lacp(self, req_lacp, src, msg):
        # ...

        # when LACP arrived at disabled port, update the status of
        # the slave i/f to enabled, and send a event.
        if not self._get_slave_enabled(dpid, port):
            self.logger.info(
                "SW=%s PORT=%d the slave i/f has just been up.",
                dpid_to_str(dpid), port)
            self._set_slave_enabled(dpid, port, True)
            self.send_event_to_observers(
                EventSlaveStateChanged(datapath, port, True))

_get_slave_enabled()メソッドは、指定したスイッチの指定したポートが有効か否
かを取得します。_set_slave_enabled()メソッドは、指定したスイッチの指定した
ポートの有効/無効状態を設定します。

上記のソースでは、無効状態のポートでLACPデータユニットを受信した場合、ポート
の状態が変更されたということを示す ``EventSlaveStateChanged`` というユーザ
定義イベントを送信しています。

.. rst-class:: sourcecode

::

    class EventSlaveStateChanged(event.EventBase):
        """a event class that notifies the changes of the statuses of the
        slave i/fs."""
        def __init__(self, datapath, port, enabled):
            """initialization."""
            super(EventSlaveStateChanged, self).__init__()
            self.datapath = datapath
            self.port = port
            self.enabled = enabled

``EventSlaveStateChanged`` イベントは、ポートが有効化したときの他に、ポート
が無効化したときにも送信されます。無効化したときの処理は
「 `FlowRemovedメッセージの受信処理`_ 」で実装されています。

``EventSlaveStateChanged`` クラスには以下の情報が含まれます。

* ポートの有効/無効状態変更が発生したOpenFlowスイッチ
* 有効/無効状態変更が発生したポート番号
* 変更後の状態


LACPデータユニットをPacket-Inさせるフローエントリの登録
"""""""""""""""""""""""""""""""""""""""""""""""""""""""

LACPデータユニットの交換間隔には、FAST（1秒ごと）とSLOW（30秒ごと）の2種類
が定義されています。リンク・アグリゲーションの仕様では、交換間隔の3倍の時間無通
信状態が続いた場合、そのインターフェースはリンク・アグリゲーションのグループ
から除外され、パケットの転送には使用されなくなります。

LACPライブラリでは、LACPデータユニット受信時にPacket-Inさせるフローエントリ
に対し、交換間隔の3倍の時間（SHORT_TIMEOUT_TIMEは3秒、LONG_TIMEOUT_TIMEは
90秒）をidle_timeoutとして設定することにより、無通信の監視を行っています。

交換間隔が変更された場合、idle_timeoutの時間も再設定する必要があるため、
LACPライブラリでは以下のような実装をしています。

.. rst-class:: sourcecode

::

    def _do_lacp(self, req_lacp, src, msg):
        # ...

        # set the idle_timeout time using the actor state of the
        # received packet.
        if req_lacp.LACP_STATE_SHORT_TIMEOUT == \
           req_lacp.actor_state_timeout:
            idle_timeout = req_lacp.SHORT_TIMEOUT_TIME
        else:
            idle_timeout = req_lacp.LONG_TIMEOUT_TIME

        # when the timeout time has changed, update the timeout time of
        # the slave i/f and re-enter a flow entry for the packet from
        # the slave i/f with idle_timeout.
        if idle_timeout != self._get_slave_timeout(dpid, port):
            self.logger.info(
                "SW=%s PORT=%d the timeout time has changed.",
                dpid_to_str(dpid), port)
            self._set_slave_timeout(dpid, port, idle_timeout)
            func = self._add_flow.get(ofproto.OFP_VERSION)
            assert func
            func(src, port, idle_timeout, datapath)

        # ...

_get_slave_timeout()メソッドは、指定したスイッチの指定したポートにおける現
在のidle_timeout値を取得します。_set_slave_timeout()メソッドは、指定したス
イッチの指定したポートにおけるidle_timeout値を登録します。初期状態および
リンク・アグリゲーション・グループから除外された場合にはidle_timeout値は0に
設定されているため、新たにLACPデータユニットを受信した場合、交換間隔がどちら
であってもフローエントリを登録します。

使用するOpenFlowのバージョンにより ``OFPFlowMod`` クラスのコンストラクタの
引数が異なるため、バージョンに応じたフローエントリ登録メソッドを取得していま
す。以下はOpenFlow 1.2以降で使用するフローエントリ登録メソッドです。

.. rst-class:: sourcecode

::

    def _add_flow_v1_2(self, src, port, timeout, datapath):
        """enter a flow entry for the packet from the slave i/f
        with idle_timeout. for OpenFlow ver1.2 and ver1.3."""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch(
            in_port=port, eth_src=src, eth_type=ether.ETH_TYPE_SLOW)
        actions = [parser.OFPActionOutput(
            ofproto.OFPP_CONTROLLER, ofproto.OFPCML_MAX)]
        inst = [parser.OFPInstructionActions(
            ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath, command=ofproto.OFPFC_ADD,
            idle_timeout=timeout, priority=65535,
            flags=ofproto.OFPFF_SEND_FLOW_REM, match=match,
            instructions=inst)
        datapath.send_msg(mod)

上記ソースで、「対向インターフェースからLACPデータユニットを受信した場合は
Packet-Inする」というフローエントリを、無通信監視時間つき最高優先度で設定
しています。


LACPデータユニットの送受信処理
""""""""""""""""""""""""""""""

LACPデータユニット受信時、「 `ポートの有効/無効状態変更に伴う処理`_ 」や
「 `LACPデータユニットをPacket-Inさせるフローエントリの登録`_ 」を行った
後、応答用のLACPデータユニットを作成し、送信します。

.. rst-class:: sourcecode

::

    def _do_lacp(self, req_lacp, src, msg):
        # ...

        # create a response packet.
        res_pkt = self._create_response(datapath, port, req_lacp)

        # packet-out the response packet.
        out_port = ofproto.OFPP_IN_PORT
        actions = [parser.OFPActionOutput(out_port)]
        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER,
            data=res_pkt.data, in_port=port, actions=actions)
        datapath.send_msg(out)

上記ソースで呼び出されている_create_response()メソッドは応答用パケット作成
処理です。その中で呼び出されている_create_lacp()メソッドで応答用のLACPデー
タユニットを作成しています。作成した応答用パケットは、LACPデータユニットを
受信したポートからPacket-Outさせます。

LACPデータユニットには送信側（Actor）の情報と受信側（Partner）の情報を設定
します。受信したLACPデータユニットの送信側情報には対向インターフェースの情報
が記載されているので、OpenFlowスイッチから応答を返すときにはそれを受信側情報
として設定します。

.. rst-class:: sourcecode

::

    def _create_lacp(self, datapath, port, req):
        """create a LACP packet."""
        actor_system = datapath.ports[datapath.ofproto.OFPP_LOCAL].hw_addr
        res = slow.lacp(
            # ...
            partner_system_priority=req.actor_system_priority,
            partner_system=req.actor_system,
            partner_key=req.actor_key,
            partner_port_priority=req.actor_port_priority,
            partner_port=req.actor_port,
            partner_state_activity=req.actor_state_activity,
            partner_state_timeout=req.actor_state_timeout,
            partner_state_aggregation=req.actor_state_aggregation,
            partner_state_synchronization=req.actor_state_synchronization,
            partner_state_collecting=req.actor_state_collecting,
            partner_state_distributing=req.actor_state_distributing,
            partner_state_defaulted=req.actor_state_defaulted,
            partner_state_expired=req.actor_state_expired,
            collector_max_delay=0)
        self.logger.info("SW=%s PORT=%d LACP sent.",
                         dpid_to_str(datapath.id), port)
        self.logger.debug(str(res))
        return res


FlowRemovedメッセージの受信処理
"""""""""""""""""""""""""""""""

指定された時間の間LACPデータユニットの交換が行われなかった場合、OpenFlowス
イッチはFlowRemovedメッセージをOpenFlowコントローラに送信します。

.. rst-class:: sourcecode

::

    @set_ev_cls(ofp_event.EventOFPFlowRemoved, MAIN_DISPATCHER)
    def flow_removed_handler(self, evt):
        """FlowRemoved event handler. when the removed flow entry was
        for LACP, set the status of the slave i/f to disabled, and
        send a event."""
        msg = evt.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        dpid = datapath.id
        match = msg.match
        if ofproto.OFP_VERSION == ofproto_v1_0.OFP_VERSION:
            port = match.in_port
            dl_type = match.dl_type
        else:
            port = match['in_port']
            dl_type = match['eth_type']
        if ether.ETH_TYPE_SLOW != dl_type:
            return
        self.logger.info(
            "SW=%s PORT=%d LACP exchange timeout has occurred.",
            dpid_to_str(dpid), port)
        self._set_slave_enabled(dpid, port, False)
        self._set_slave_timeout(dpid, port, 0)
        self.send_event_to_observers(
            EventSlaveStateChanged(datapath, port, False))

FlowRemovedメッセージを受信すると、OpenFlowコントローラは
_set_slave_enabled()メソッドを使用してポートの無効状態を設定し、
_set_slave_timeout()メソッドを使用してidle_timeout値を0に設定し、
send_event_to_observers()メソッドを使用して ``EventSlaveStateChanged``
イベントを送信します。


アプリケーションの実装
^^^^^^^^^^^^^^^^^^^^^^

「 `Ryuアプリケーションの実行`_ 」に示したOpenFlow 1.3対応のリンク・アグリ
ゲーション・アプリケーション (simple_switch_lacp_13.py) と、
「 :ref:`ch_switching_hub` 」のスイッチングハブとの差異を順に説明していき
ます。


「_CONTEXTS」の設定
"""""""""""""""""""

ryu.base.app_manager.RyuAppを継承したRyuアプリケーションは、「_CONTEXTS」
ディクショナリに他のRyuアプリケーションを設定することにより、他のアプリケー
ションを別スレッドで起動させることができます。ここではLACPライブラリの
LacpLibクラスを「lacplib」という名前で「_CONTEXTS」に設定しています。

.. rst-class:: sourcecode

::

    from ryu.lib import lacplib

    # ...

    class SimpleSwitchLacp13(app_manager.RyuApp):
        OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
        _CONTEXTS = {'lacplib': lacplib.LacpLib}

        # ...


「_CONTEXTS」に設定したアプリケーションは、__init__()メソッドのkwargsから
インスタンスを取得することができます。


.. rst-class:: sourcecode

::

        # ...
        def __init__(self, *args, **kwargs):
            super(SimpleSwitchLacp13, self).__init__(*args, **kwargs)
            self.mac_to_port = {}
            self._lacp = kwargs['lacplib']
        # ...


ライブラリの初期設定
""""""""""""""""""""

「_CONTEXTS」に設定したLACPライブラリの初期設定を行います。初期設定には
LACPライブラリの提供するadd()メソッドを実行します。ここでは以下の値を設定し
ます。

============ ================================= ==============================
パラメータ   値                                説明
============ ================================= ==============================
dpid         str_to_dpid('0000000000000001')   データパスID
ports        [1, 2]                            グループ化するポートのリスト
============ ================================= ==============================

この設定により、データパスID「0000000000000001」のOpenFlowスイッチのポート1と
ポート2がひとつのリンク・アグリゲーション・グループとして動作します。


.. rst-class:: sourcecode

::

        # ...
            self._lacp = kwargs['lacplib']
            self._lacp.add(
                dpid=str_to_dpid('0000000000000001'), ports=[1, 2])
        # ...


ユーザ定義イベントの受信方法
""""""""""""""""""""""""""""

`LACPライブラリの実装`_ で説明したとおり、LACPライブラリはLACPデータユニッ
トの含まれないPacket-Inメッセージを ``EventPacketIn`` というユーザ定義イ
ベントとして送信します。ユーザ定義イベントのイベントハンドラも、Ryuが提供す
るイベントハンドラと同じように ``ryu.controller.handler.set_ev_cls`` デコ
レータで装飾します。

.. rst-class:: sourcecode

::

    @set_ev_cls(lacplib.EventPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        # ...

また、LACPライブラリはポートの有効/無効状態が変更されると
``EventSlaveStateChanged`` イベントを送信しますので、こちらもイベントハンド
ラを作成しておきます。

.. rst-class:: sourcecode

::

    @set_ev_cls(lacplib.EventSlaveStateChanged, lacplib.LAG_EV_DISPATCHER)
    def _slave_state_changed_handler(self, ev):
        datapath = ev.datapath
        dpid = datapath.id
        port_no = ev.port
        enabled = ev.enabled
        self.logger.info("slave state changed port: %d enabled: %s",
                         port_no, enabled)
        if dpid in self.mac_to_port:
            for mac in self.mac_to_port[dpid]:
                match = datapath.ofproto_parser.OFPMatch(eth_dst=mac)
                self.del_flow(datapath, match)
            del self.mac_to_port[dpid]
        self.mac_to_port.setdefault(dpid, {})

本節の冒頭で説明したとおり、ポートの有効/無効状態が変更され
ると、論理インターフェースを通
過するパケットが実際に使用する物理インターフェースが変更になる可能性がありま
す。そのため、登録されているフローエントリを全て削除
しています。

.. rst-class:: sourcecode

::

    def del_flow(self, datapath, match):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        mod = parser.OFPFlowMod(datapath=datapath,
                                command=ofproto.OFPFC_DELETE,
                                match=match)
        datapath.send_msg(mod)

フローエントリの削除は ``OFPFlowMod`` クラスのインスタンスで行います。

以上のように、リンク・アグリゲーション機能を提供するライブラリと、ライブラリ
を利用するアプリケーションによって、リンク・アグリゲーション機能を持つスイッ
チングハブのアプリケーションを実現しています。


まとめ
------

本章では、リンク・アグリゲーションライブラリの利用を題材として、以下の項目に
ついて説明しました。

* 「_CONTEXTS」を用いたライブラリの使用方法
* ユーザ定義イベントの定義方法とイベントトリガーの発生方法
