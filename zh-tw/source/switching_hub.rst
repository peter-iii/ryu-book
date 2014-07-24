.. _ch_switching_hub:

Switching Hub
================

本章將會以簡單的 Switching hub 安裝作為題材，說明 Ryu 如何安裝一個應用程式。

Switching Hub
----------------

在交換器中有許許多多的功能。在這邊我們將看到擁有下列簡單功能的交換器。

* 學習所連接 port 的 host 其 MAC 位址，並記錄在 MAC位址表當中。
* 對於已經記錄下來的 MAC 位址，若是收到送往該 MAC 位址的封包，則轉送該封包到相對應的埠。
* 對於未指定目標位址的封包，則執行 Flooding。

讓我們使用 Ryu 來實現這樣一個交換器吧。


OpenFlow 實作的交換器
------------------------------

OpenFlow 交換器會接受來自于 controller 的指令並達到以下功能。，

* 對於接收到的封包進行修改，或針對指定的埠進行轉送。
* 對於接收到的封包進行轉送到 conteroller 的動作 (Packet-In)
* 對於接收到來自 controller 的封包轉送到指定的埠 (Packet-Out)

上述的功能組合起來的話就是一台交換器的實現。

首先，利用 Packet-In 的功能來達到 MAC 位址的學習。
controller 使用 Packet-In 接收來自交換器的封包之後進行分析，得到埠的相關資料以及所連接 host 的 MAC 位址。

在學習之後，就會對所收到的封包進行轉送。
所以將封包的目的位址，在已經學習的 host 資料中進行檢索，根據檢索的結過會進行下列處理。

* 如果是已經存在記錄中的 host：使用 Packet-Out 功能轉送至先前所對應的埠
* 如果是尚未存在記錄中的 host：使用 Packet-Out 功能來達到 Flooding

下面將一步一步的說明並附上圖片以幫助理解。


1. 初始狀態

    Flow table 為空白的狀況。

    將 host A 連接到埠 1，host B 連接到埠 4，host C 連接到埠 3。

    .. only:: latex

       .. image:: images/switching_hub/fig1.eps
          :scale: 80 %
          :align: center

    .. only:: not latex

       .. image:: images/switching_hub/fig1.png
          :align: center


2. host A → host B

    當 host A 向 host B 發送封包。這時會觸發 Packet-In 訊息。host A 的 MAC 位址會被埠 1 給記錄下來。
    由於 host B 的 MAC 位址尚未被學習，因此將會進行 Flooding 並將封包往 host B 和 host c 發送。

    .. only:: latex

       .. image:: images/switching_hub/fig2.eps
          :scale: 80 %
          :align: center

    .. only:: not latex

       .. image:: images/switching_hub/fig2.png
          :align: center

    Packet-In::

        in-port: 1
        eth-dst: host B
        eth-src: host A

    Packet-Out::

        action: OUTPUT: Flooding


3. host B → host A

    封包從 host B 向 host A 返回時，在 Flow Table 中新增一筆 Flow Entry，並將封包轉送到埠 1 。
    因此，該封包並不會被 host C 收到。

    .. only:: latex

       .. image:: images/switching_hub/fig3.eps
          :scale: 80 %
          :align: center

    .. only:: not latex

       .. image:: images/switching_hub/fig3.png
          :align: center


    Packet-In::

        in-port: 4
        eth-dst: host A
        eth-src: host B

    Packet-Out::

        action: OUTPUT: port 1


4. host A → host B

    再次， host A 向 host B 發送封包，在 Flow Table 新增一個 Flow Entry 接著轉送封包到埠 4。

    .. only:: latex

       .. image:: images/switching_hub/fig4.eps
          :scale: 80 %
          :align: center

    .. only:: not latex

       .. image:: images/switching_hub/fig4.png
          :align: center


    Packet-In::

        in-port: 1
        eth-dst: host B
        eth-src: host A

    Packet-Out::

        action: OUTPUT: port 4

接下來，讓我們實際來看一下在 Ryu 當中實作交換器的原始碼。


在Ryu上實作交換器
-------------------------------

交換器的原始碼在 Ryu 的原始碼之中有提供。

    ryu/app/simple_switch_13.py

OpenFlow 其他的版本也有相對應的原始碼，例如 simple_switch.py(OpenFlow 1.0) 和 simple_switch_12.py(OpenFlow 1.2)。我們現在要來看的則是 OpenFlow 1.3 的版本。

由於原始碼不多，因此我們把全部拿來檢視。

.. rst-class:: sourcecode

.. literalinclude:: sources/simple_switch_13.py

那麼，我們開始看一下其中的內容吧。


類別的定義和初始化
^^^^^^^^^^^^^^^^^^^^

為了要實作 Ryu 應用程式，因此繼承了 ryu.base.app_manager.RyuApp。
接著為了使用 OpenFlow 1.3 ，將 ``OFP_VERSIONS`` 指定為 OpenFlow 1.3。

然後，MAC 位址表也 mac_to_port 也已經定義。

OpenFlow通訊協定中有些程序像是握手協定，是讓 OpenFlow 交換器和 controller 之間進行通訊時使用且被定義好的。
但是這些細節，對於一個 Ryu 應用程式來說是不擁要擔心或特別處理的。


.. rst-class:: sourcecode

::

    class SimpleSwitch13(app_manager.RyuApp):
        OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

        def __init__(self, *args, **kwargs):
            super(SimpleSwitch13, self).__init__(*args, **kwargs)
            self.mac_to_port = {}

        # ...


事件管理(Event handler)
^^^^^^^^^^^^^^^^

對於 Ryu 來說，接受到一個 OpenFlow訊息即會產生一個相對應的事件。而 Ryu 應用程式則是必須實作事件管理以處理相對應發生的事件。

事件管理(Event Handler)是一個擁有事件物件(Event Object)做為參數，並且使用``ryu.controller.handler.set_ev_cls`` 修飾(Decorator)的函數。

set_ev_cls 則指定事件類別得以接受訊息和交換器狀態作為參數。

事件類別名稱的規則為 ``ryu.controller.ofp_event.EventOFP`` + <OpenFlow訊息名稱>，
例如：在 Packet-In 訊息的狀態下則為 ``EventOFPPacketIn`` 。
詳細的內容請參考 Ryu 的文件 `API reference <http://ryu.readthedocs.org/en/latest/>`_ 。
對於狀態來說，請指定下述列表中的一項。

.. tabularcolumns:: |l|L|

=========================================== ==================================
定義                                        説明
=========================================== ==================================
ryu.controller.handler.HANDSHAKE_DISPATCHER 交換 HELLO 訊息
ryu.controller.handler.CONFIG_DISPATCHER    接收 SwitchFeatures訊息
ryu.controller.handler.MAIN_DISPATCHER      一般狀態
ryu.controller.handler.DEAD_DISPATCHER      連線中斷
=========================================== ==================================


新增 Table-miss Flow Entry 
""""""""""""""""""""""""""""""

OpenFlow 交換器的握手協議完成之後新增 Table-miss Flow Entry 到 Flow Table 中為接收 Packet-In 訊息做準備。

具體來說，接收到 Switch Features(Features Reply) 訊息後就會新增 Table-miss Flow Entry。

.. rst-class:: sourcecode

::

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # ...

``ev.msg``是用來儲存對應事件的 OpenFlow 訊息類別實體。
在這個例子中則是 ``ryu.ofproto.ofproto_v1_3_parser.OFPSwitchFeatures``。

``msg.datapath`` 這個訊息是用來儲存 OpenFlow 交換器的 ``ryu.controller.controller.Datapath`` 類別所對應的實體。

Datapath 類別是用來處理 OpenFlow 交換器重要的訊息，例如執行與交換器的通訊和觸發接收訊息相關的事件。

Ryu 應用程式所使用的主要屬性如下：

.. tabularcolumns:: |l|L|

============== ==============================================================
属性名稱         説明
============== ==============================================================
id             連接 OpenFlow 交換器的 ID(datapath ID)。
ofproto        表示使用的 OpenFlow 版本所對應的 ofproto module。
               目前的狀況下是下述的其中之一。

               ``ryu.ofproto.ofproto_v1_0``

               ``ryu.ofproto.ofproto_v1_2``

               ``ryu.ofproto.ofproto_v1_3``

               ``ryu.ofproto.ofproto_v1_4``

ofproto_parser 和 ofproto 一樣，表示 ofproto_parser module。
               在目前的狀況下，會是下述之一。

               ``ryu.ofproto.ofproto_v1_0_parser``

               ``ryu.ofproto.ofproto_v1_2_parser``

               ``ryu.ofproto.ofproto_v1_3_parser``

               ``ryu.ofproto.ofproto_v1_4_parser``
============== ==============================================================

Ryu 應用程式中 Datapath 類別的主要方法如下：

send_msg(msg)

    發送 OpenFlow 訊息。
    msg 是發送 OpenFlow 訊息的 
    ``ryu.ofproto.ofproto_parser.MsgBase`` 類別的子類別。


交換器本身不僅僅使用 Switch Features 訊息。
使用事件處理以取得新增 Table-miss Flow Entry 的時間點。

.. rst-class:: sourcecode

::

    def switch_features_handler(self, ev):
        # ...

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

Table-miss Flow Entry 的優先權為 0 ，即最低的優先權，而且此 Entry 可以 match 所有的封包。
這個 Entry 的 Instruction 通常指定為 output action ，並且輸出的埠將指向 controller。
因此當封包沒有 match 任何一個普通 Flow 時，則觸發 Packet-In 。


.. NOTE::

    目前(2014年1月)，市面上的 Open vSwitch 對於 OpenFlow 1.3 的支援並不完整
    對於 OpenFlow 1.3 以前的版本 Packet-In 是個基本的功能。
    而且 Table-miss Flow Entry 也尚未被支援，僅僅使用一般的 Flow Entry 取代。

為了 match 所有的封包，空的 match 將被使用。match 表示於 ``OFPMatch`` 類別中。

接下來，為了轉送到 controller 埠， OUTPUT action 類別(``OFPActionOutput``)的實例將會被產生。
Controller 會被指定為封包的目的地，``OFPCML_NO_BUFFER`` 會被設定為 max_len 以便接下來的封包傳送。


.. NOTE::

    送往 controller 的封包可以僅傳送 header 部分(Ethernet header)，剩下的則存在緩衝區間中以增加效率。
    但目前 (2014年1月) Open vSwitch 的臭蟲關係，會將所有的封包傳送。

最後，設定優先權為0(最低優先權)。然後執行 ``add_flow()`` 方法以發送 Flow Mod 訊息。
add_flow()方法的內容將會在稍後進行說明。


Packet-in 訊息
"""""""""""""""""""

為了接收處理未知目的地的封包，需要 Packet-In 事件管理。

.. rst-class:: sourcecode

::

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # ...


OFPPacketIn 類別經常使用的屬性如下所示。

.. tabularcolumns:: |l|L|

========= ===================================================================
屬性名稱    説明
========= ===================================================================
match     ``ryu.ofproto.ofproto_v1_3_parser.OFPMatch`` 類別的實體，其中儲存接收封包的 Meta 資訊。
data      接收封包本身的 binary 資料
total_len 接收封包的資料長度
buffer_id 接收封包的內容若是存在 OpenFlow 交換器上，所指定的ID
          如果沒有 buffer 的狀況下，則設定 ``ryu.ofproto.ofproto_v1_3.OFP_NO_BUFFER``
========= ===================================================================


MAC address table 更新
"""""""""""""""""""""""""

.. rst-class:: sourcecode

::

    def _packet_in_handler(self, ev):
        # ...

        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        # ...

從 OFPPacketIn 類別的 match 得到接收埠(``in_port``)的資訊。
目標 MAC address 和來源 MAC address 使用 Ryu 的封包函式庫，從接收到的封包的 Ethernet header 取得。

藉由得知目標 Mac address 和來源 Mac address，更新 MAC address table。

為了可以對應連接到多個 OpenFlow 交換器，Mac address table 和每一個交換器之間的識別，就使用 datapath ID來辨認。


判斷轉送封包的埠
""""""""""""""""""

宛先MACアドレスが、MACアドレステーブルに存在する場合は対応するポート番号を、
見つからなかった場合はフラッディング(``OFPP_FLOOD``)を出力ポートに指定した
OUTPUTアクションクラスのインスタンスを生成します。

.. rst-class:: sourcecode

::

    def _packet_in_handler(self, ev):
        # ...

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            self.add_flow(datapath, 1, match, actions)

        # ...


宛先MACアドレスが見つかった場合は、OpenFlowスイッチのフローテーブルに
エントリを追加します。

Table-missフローエントリの追加と同様に、マッチとアクションを指定して
add_flow()を実行し、フローエントリを追加します。

Table-missフローエントリとは違って、今回はマッチに条件を設定します。
今回のスイッチングハブの実装では、受信ポート(in_port)と宛先MACアドレス
(eth_dst)を指定しています。例えば、「ポート1で受信したホストB宛」のパケット
が対象となります。

今回のフローエントリでは、優先度に1を指定しています。値が大きい
ほど優先度が高くなるので、ここで追加するフローエントリは、Table-missフロー
エントリより先に評価されるようになります。

前述のアクションを含めてまとめると、以下のようなエントリをフローテーブル
に追加します。

    ポート1で受信した、ホストB宛(宛先MACアドレスがB)のパケットを、
    ポート4に転送する

.. HINT::

    OpenFlowでは、NORMALポートという論理的な出力ポートがオプションで規定
    されており、出力ポートにNORMALを指定すると、スイッチのL2/L3機能を使っ
    てパケットを処理するようになります。つまり、すべてのパケットをNORMAL
    ポートに出力するように指示するだけで、スイッチングハブとして動作する
    ようにできますが、ここでは各々の処理をOpenFlowを使って実現するものとします。


フローエントリの追加処理
""""""""""""""""""""""""

Packet-Inハンドラの処理がまだ終わっていませんが、ここで一旦フローエントリ
を追加するメソッドの方を見ていきます。

.. rst-class:: sourcecode

::

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]

        # ...

フローエントリには、対象となるパケットの条件を示すマッチと、そのパケット
に対する操作を示すインストラクション、エントリの優先度、有効時間などを
設定します。

スイッチングハブの実装では、インストラクションにApply Actionsを使用して、
指定したアクションを直ちに適用するように設定しています。

最後に、Flow Modメッセージを発行してフローテーブルにエントリを追加します。

.. rst-class:: sourcecode

::

    def add_flow(self, datapath, port, dst, actions):
        # ...

        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

Flow Modメッセージに対応するクラスは ``OFPFlowMod`` クラスです。OFPFlowMod
クラスのインスタンスを生成して、Datapath.send_msg() メソッドでOpenFlow
スイッチにメッセージを送信します。

OFPFlowModクラスのコンストラクタには多くの引数がありますが、多くのものは
大抵の場合、デフォルト値のままで済みます。かっこ内はデフォルト値です。

datapath

    フローテーブルを操作する対象となるOpenFlowスイッチに対応するDatapath
    クラスのインスタンスです。通常は、Packet-Inメッセージなどのハンドラ
    に渡されるイベントから取得したものを指定します。

cookie (0)

    コントローラが指定する任意の値で、エントリの更新または削除を行う際の
    フィルタ条件として使用できます。パケットの処理では使用されません。

cookie_mask (0)

    エントリの更新または削除の場合に、0以外の値を指定すると、エントリの
    cookie値による操作対象エントリのフィルタとして使用されます。

table_id (0)

    操作対象のフローテーブルのテーブルIDを指定します。

command (ofproto_v1_3.OFPFC_ADD)

    どのような操作を行うかを指定します。

    ==================== ========================================
    値                   説明
    ==================== ========================================
    OFPFC_ADD            新しいフローエントリを追加します
    OFPFC_MODIFY         フローエントリを更新します
    OFPFC_MODIFY_STRICT  厳格に一致するフローエントリを更新します
    OFPFC_DELETE         フローエントリを削除します
    OFPFC_DELETE_STRICT  厳格に一致するフローエントリを削除します
    ==================== ========================================

idle_timeout (0)

    このエントリの有効期限を秒単位で指定します。エントリが参照されずに
    idle_timeoutで指定した時間を過ぎた場合、そのエントリは削除されます。
    エントリが参照されると経過時間はリセットされます。

    エントリが削除されるとFlow Removedメッセージがコントローラに通知され
    ます。

hard_timeout (0)

    このエントリの有効期限を秒単位で指定します。idle_timeoutと違って、
    hard_timeoutでは、エントリが参照されても経過時間はリセットされません。
    つまり、エントリの参照の有無に関わらず、指定された時間が経過すると
    エントリが削除されます。

    idle_timeoutと同様に、エントリが削除されるとFlow Removedメッセージが
    通知されます。

priority (0)

    このエントリの優先度を指定します。
    値が大きいほど、優先度も高くなります。

buffer_id (ofproto_v1_3.OFP_NO_BUFFER)

    OpenFlowスイッチ上でバッファされたパケットのバッファIDを指定します。
    バッファIDはPacket-Inメッセージで通知されたものであり、指定すると
    OFPP_TABLEを出力ポートに指定したPacket-OutメッセージとFlow Modメッセージ
    の2つのメッセージを送ったのと同じように処理されます。
    commandがOFPFC_DELETEまたはOFPFC_DELETE_STRICTの場合は無視されます。

    バッファIDを指定しない場合は、 ``OFP_NO_BUFFER`` をセットします。

out_port (0)

    OFPFC_DELETEまたはOFPFC_DELETE_STRICTの場合に、対象となるエントリを
    出力ポートでフィルタします。OFPFC_ADD、OFPFC_MODIFY、OFPFC_MODIFY_STRICT
    の場合は無視されます。

    出力ポートでのフィルタを無効にするには、 ``OFPP_ANY`` を指定します。

out_group (0)

    out_portと同様に、出力グループでフィルタします。

    無効にするには、 ``OFPG_ANY`` を指定します。

flags (0)

    以下のフラグの組み合わせを指定することができます。

    .. tabularcolumns:: |l|L|

    ===================== ===================================================
    値                    説明
    ===================== ===================================================
    OFPFF_SEND_FLOW_REM   このエントリが削除された時に、コントローラにFlow
                          Removedメッセージを発行します。
    OFPFF_CHECK_OVERLAP   OFPFC_ADDの場合に、重複するエントリのチェックを行い
                          ます。重複するエントリがあった場合にはFlow Modは失
                          敗し、エラーが返されます。
    OFPFF_RESET_COUNTS    該当エントリのパケットカウンタとバイトカウンタを
                          リセットします。
    OFPFF_NO_PKT_COUNTS   このエントリのパケットカウンタを無効にします。
    OFPFF_NO_BYT_COUNTS   このエントリのバイトカウンタを無効にします。
    ===================== ===================================================

match (None)

    マッチを指定します。

instructions ([])

    インストラクションのリストを指定します。


パケットの転送
""""""""""""""

Packet-Inハンドラに戻り、最後の処理の説明です。

宛先MACアドレスがMACアドレステーブルから見つかったかどうかに関わらず、最終的
にはPacket-Outメッセージを発行して、受信パケットを転送します。

.. rst-class:: sourcecode

::

    def _packet_in_handler(self, ev):
        # ...

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

Packet-Outメッセージに対応するクラスは ``OFPPacketOut`` クラスです。

OFPPacketOutのコンストラクタの引数は以下のようになっています。

datapath

    OpenFlowスイッチに対応するDatapathクラスのインスタンスを指定します。

buffer_id

    OpenFlowスイッチ上でバッファされたパケットのバッファIDを指定します。
    バッファを使用しない場合は、 ``OFP_NO_BUFFER`` を指定します。

in_port

    パケットを受信したポートを指定します。受信パケットでない場合は、
    ``OFPP_CONTROLLER`` を指定します。

actions

    アクションのリストを指定します。

data

    パケットのバイナリデータを指定します。buffer_idに ``OFP_NO_BUFFER``
    が指定された場合に使用されます。OpenFlowスイッチのバッファを利用す
    る場合は省略します。


スイッチングハブの実装では、buffer_idにPacket-Inメッセージのbuffer_idを
指定しています。Packet-Inメッセージのbuffer_idが無効だった場合は、
Packet-Inの受信パケットをdataに指定して、パケットを送信しています。


これで、スイッチングハブのソースコードの説明は終わりです。
次は、このスイッチングハブを実行して、実際の動作を確認します。


Ryuアプリケーションの実行
-------------------------

スイッチングハブの実行のため、OpenFlowスイッチにはOpen vSwitch、実行
環境としてmininetを使います。

Ryu用のOpenFlow Tutorial VMイメージが用意されているので、このVMイメージ
を利用すると実験環境を簡単に準備することができます。

VMイメージ

    http://sourceforge.net/projects/ryu/files/vmimages/OpenFlowTutorial/

    OpenFlow_Tutorial_Ryu3.2.ova (約1.4GB)

関連ドキュメント(Wikiページ)

    https://github.com/osrg/ryu/wiki/OpenFlow_Tutorial

ドキュメントにあるVMイメージは、Open vSwitchとRyuのバージョンが古いため
ご注意ください。


このVMイメージを使わず、自分で環境を構築することも当然できます。VMイメージ
で使用している各ソフトウェアのバージョンは以下の通りですので、自身で構築
する場合は参考にしてください。

Mininet VM バージョン2.0.0
  http://mininet.org/download/

Open vSwitch バージョン1.11.0
  http://openvswitch.org/download/

Ryu バージョン3.2
  https://github.com/osrg/ryu/

    .. rst-class:: console

    ::

        $ sudo pip install ryu


ここでは、Ryu用OpenFlow TutorialのVMイメージを利用します。

Mininetの実行
^^^^^^^^^^^^^

mininetからxtermを起動するため、Xが使える環境が必要です。

ここでは、OpenFlow TutorialのVMを利用しているため、
sshでX11 Forwardingを有効にしてログインします。

    ::

        $ ssh -X ryu@<VMのアドレス>

ユーザー名は ``ryu`` 、パスワードも ``ryu`` です。


ログインできたら、 ``mn`` コマンドによりMininet環境を起動します。

構築する環境は、ホスト3台、スイッチ1台のシンプルな構成です。

mnコマンドのパラメータは、以下のようになります。

============ ========== ===========================================
パラメータ   値         説明
============ ========== ===========================================
topo         single,3   スイッチが1台、ホストが3台のトポロジ
mac          なし       自動的にホストのMACアドレスをセットする
switch       ovsk       Open vSwitchを使用する
controller   remote     OpenFlowコントローラは外部のものを利用する
x            なし       xtermを起動する
============ ========== ===========================================

実行例は以下のようになります。

.. rst-class:: console

::

    $ sudo mn --topo single,3 --mac --switch ovsk --controller remote -x
    *** Creating network
    *** Adding controller
    Unable to contact the remote controller at 127.0.0.1:6633
    *** Adding hosts:
    h1 h2 h3
    *** Adding switches:
    s1
    *** Adding links:
    (h1, s1) (h2, s1) (h3, s1)
    *** Configuring hosts
    h1 h2 h3
    *** Running terms on localhost:10.0
    *** Starting controller
    *** Starting 1 switches
    s1
    *** Starting CLI:
    mininet>

実行するとデスクトップPC上でxtermが5つ起動します。
それぞれ、ホスト1～3、スイッチ、コントローラに対応します。

スイッチのxtermからコマンドを実行して、使用するOpenFlowのバージョンを
セットします。ウインドウタイトルが「switch: s1 (root)」となっている
ものがスイッチ用のxtermです。

まずはOpen vSwitchの状態を見てみます。

switch: s1:

.. rst-class:: console

::

    root@ryu-vm:~# ovs-vsctl show
    fdec0957-12b6-4417-9d02-847654e9cc1f
    Bridge "s1"
        Controller "ptcp:6634"
        Controller "tcp:127.0.0.1:6633"
        fail_mode: secure
        Port "s1-eth3"
            Interface "s1-eth3"
        Port "s1-eth2"
            Interface "s1-eth2"
        Port "s1-eth1"
            Interface "s1-eth1"
        Port "s1"
            Interface "s1"
                type: internal
    ovs_version: "1.11.0"
    root@ryu-vm:~# ovs-dpctl show
    system@ovs-system:
            lookups: hit:14 missed:14 lost:0
            flows: 0
            port 0: ovs-system (internal)
            port 1: s1 (internal)
            port 2: s1-eth1
            port 3: s1-eth2
            port 4: s1-eth3
    root@ryu-vm:~#

スイッチ(ブリッジ) *s1* ができていて、ホストに対応するポートが
3つ追加されています。

次にOpenFlowのバージョンとして1.3を設定します。

switch: s1:

.. rst-class:: console

::

    root@ryu-vm:~# ovs-vsctl set Bridge s1 protocols=OpenFlow13
    root@ryu-vm:~#

空のフローテーブルを確認してみます。

switch: s1:

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O OpenFlow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
    root@ryu-vm:~#

ovs-ofctlコマンドには、オプションで使用するOpenFlowのバージョンを
指定する必要があります。デフォルトは *OpenFlow10* です。


スイッチングハブの実行
^^^^^^^^^^^^^^^^^^^^^^

準備が整ったので、Ryuアプリケーションを実行します。

ウインドウタイトルが「controller: c0 (root)」となっているxtermから
次のコマンドを実行します。

controller: c0:

.. rst-class:: console

::

    root@ryu-vm:~# ryu-manager --verbose ryu.app.simple_switch_13
    loading app ryu.app.simple_switch_13
    loading app ryu.controller.ofp_handler
    instantiating app ryu.app.simple_switch_13
    instantiating app ryu.controller.ofp_handler
    BRICK SimpleSwitch13
      CONSUMES EventOFPSwitchFeatures
      CONSUMES EventOFPPacketIn
    BRICK ofp_event
      PROVIDES EventOFPSwitchFeatures TO {'SimpleSwitch13': set(['config'])}
      PROVIDES EventOFPPacketIn TO {'SimpleSwitch13': set(['main'])}
      CONSUMES EventOFPErrorMsg
      CONSUMES EventOFPHello
      CONSUMES EventOFPEchoRequest
      CONSUMES EventOFPPortDescStatsReply
      CONSUMES EventOFPSwitchFeatures
    connected socket:<eventlet.greenio.GreenSocket object at 0x2e2c050> address:('127.0.0.1', 53937)
    hello ev <ryu.controller.ofp_event.EventOFPHello object at 0x2e2a550>
    move onto config mode
    EVENT ofp_event->SimpleSwitch13 EventOFPSwitchFeatures
    switch features ev version: 0x4 msg_type 0x6 xid 0xff9ad15b OFPSwitchFeatures(auxiliary_id=0,capabilities=71,datapath_id=1,n_buffers=256,n_tables=254)
    move onto main mode

OVSとの接続に時間がかかる場合がありますが、少し待つと上のように

.. rst-class:: console

::

    connected socket:<....
    hello ev ...
    ...
    move onto main mode

と表示されます。

これで、OVSと接続し、ハンドシェイクが行われ、Table-missフローエントリが
追加され、Packet-Inを待っている状態になっています。

Table-missフローエントリが追加されていることを確認します。

switch: s1:

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x0, duration=105.975s, table=0, n_packets=0, n_bytes=0, priority=0 actions=CONTROLLER:65535
    root@ryu-vm:~#

優先度が0で、マッチがなく、アクションにCONTROLLER、送信データサイズ65535
(0xffff = OFPCML_NO_BUFFER)が指定されています。


動作の確認
^^^^^^^^^^

ホスト1からホスト2へpingを実行します。

1. ARP request

    この時点では、ホスト1はホスト2のMACアドレスを知らないので、ICMP echo
    requestに先んじてARP requestをブロードキャストするはずです。
    このブロードキャストパケットはホスト2とホスト3で受信されます。

2. ARP reply

    ホスト2がARPに応答して、ホスト1にARP replyを返します。

3. ICMP echo request

    これでホスト1はホスト2のMACアドレスを知ることができたので、echo request
    をホスト2に送信します。

4. ICMP echo reply

    ホスト2はホスト1のMACアドレスを既に知っているので、echo replyをホスト1
    に返します。

このような通信が行われるはずです。

pingコマンドを実行する前に、各ホストでどのようなパケットを受信したかを確認
できるようにtcpdumpコマンドを実行しておきます。

host: h1:

.. rst-class:: console

::

    root@ryu-vm:~# tcpdump -en -i h1-eth0
    tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
    listening on h1-eth0, link-type EN10MB (Ethernet), capture size 65535 bytes

host: h2:

.. rst-class:: console

::

    root@ryu-vm:~# tcpdump -en -i h2-eth0
    tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
    listening on h2-eth0, link-type EN10MB (Ethernet), capture size 65535 bytes

host: h3:

.. rst-class:: console

::

    root@ryu-vm:~# tcpdump -en -i h3-eth0
    tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
    listening on h3-eth0, link-type EN10MB (Ethernet), capture size 65535 bytes


それでは、最初にmnコマンドを実行したコンソールで、次のコマンドを実行して
ホスト1からホスト2へpingを発行します。

.. rst-class:: console

::

    mininet> h1 ping -c1 h2
    PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
    64 bytes from 10.0.0.2: icmp_req=1 ttl=64 time=97.5 ms

    --- 10.0.0.2 ping statistics ---
    1 packets transmitted, 1 received, 0% packet loss, time 0ms
    rtt min/avg/max/mdev = 97.594/97.594/97.594/0.000 ms
    mininet>


ICMP echo replyは正常に返ってきました。

まずはフローテーブルを確認してみましょう。

switch: s1:

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x0, duration=417.838s, table=0, n_packets=3, n_bytes=182, priority=0 actions=CONTROLLER:65535
     cookie=0x0, duration=48.444s, table=0, n_packets=2, n_bytes=140, priority=1,in_port=2,dl_dst=00:00:00:00:00:01 actions=output:1
     cookie=0x0, duration=48.402s, table=0, n_packets=1, n_bytes=42, priority=1,in_port=1,dl_dst=00:00:00:00:00:02 actions=output:2
    root@ryu-vm:~#

Table-missフローエントリ以外に、優先度が1のフローエントリが2つ登録されて
います。

(1) 受信ポート(in_port):2, 宛先MACアドレス(dl_dst):ホスト1 →
    動作(actions):ポート1に転送
(2) 受信ポート(in_port):1, 宛先MACアドレス(dl_dst):ホスト2 →
    動作(actions):ポート2に転送

(1)のエントリは2回参照され(n_packets)、(2)のエントリは1回参照されています。
(1)はホスト2からホスト1宛の通信なので、ARP replyとICMP echo replyの2つが
マッチしたものでしょう。
(2)はホスト1からホスト2宛の通信で、ARP requestはブロードキャストされるので、
これはICMP echo requestによるもののはずです。


それでは、simple_switch_13のログ出力を見てみます。

controller: c0:

.. rst-class:: console

::

    EVENT ofp_event->SimpleSwitch13 EventOFPPacketIn
    packet in 1 00:00:00:00:00:01 ff:ff:ff:ff:ff:ff 1
    EVENT ofp_event->SimpleSwitch13 EventOFPPacketIn
    packet in 1 00:00:00:00:00:02 00:00:00:00:00:01 2
    EVENT ofp_event->SimpleSwitch13 EventOFPPacketIn
    packet in 1 00:00:00:00:00:01 00:00:00:00:00:02 1


1つ目のPacket-Inは、ホスト1が発行したARP requestで、ブロードキャストなので
フローエントリは登録されず、Packet-Outのみが発行されます。

2つ目は、ホスト2から返されたARP replyで、宛先MACアドレスがホスト1となって
いるので前述のフローエントリ(1)が登録されます。

3つ目は、ホスト1からホスト2へ送信されたICMP echo requestで、フローエントリ
(2)が登録されます。

ホスト2からホスト1に返されたICMP echo replyは、登録済みのフローエントリ(1)
にマッチするため、Packet-Inは発行されずにホスト1へ転送されます。


最後に各ホストで実行したtcpdumpの出力を見てみます。

host: h1:

.. rst-class:: console

::

    root@ryu-vm:~# tcpdump -en -i h1-eth0
    tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
    listening on h1-eth0, link-type EN10MB (Ethernet), capture size 65535 bytes
    20:38:04.625473 00:00:00:00:00:01 > ff:ff:ff:ff:ff:ff, ethertype ARP (0x0806), length 42: Request who-has 10.0.0.2 tell 10.0.0.1, length 28
    20:38:04.678698 00:00:00:00:00:02 > 00:00:00:00:00:01, ethertype ARP (0x0806), length 42: Reply 10.0.0.2 is-at 00:00:00:00:00:02, length 28
    20:38:04.678731 00:00:00:00:00:01 > 00:00:00:00:00:02, ethertype IPv4 (0x0800), length 98: 10.0.0.1 > 10.0.0.2: ICMP echo request, id 3940, seq 1, length 64
    20:38:04.722973 00:00:00:00:00:02 > 00:00:00:00:00:01, ethertype IPv4 (0x0800), length 98: 10.0.0.2 > 10.0.0.1: ICMP echo reply, id 3940, seq 1, length 64


ホスト1では、最初にARP requestがブロードキャストされていて、続いてホスト2から
返されたARP replyを受信しています。
次にホスト1が発行したICMP echo request、ホスト2から返されたICMP echo replyが
受信されています。

host: h2:

.. rst-class:: console

::

    root@ryu-vm:~# tcpdump -en -i h2-eth0
    tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
    listening on h2-eth0, link-type EN10MB (Ethernet), capture size 65535 bytes
    20:38:04.637987 00:00:00:00:00:01 > ff:ff:ff:ff:ff:ff, ethertype ARP (0x0806), length 42: Request who-has 10.0.0.2 tell 10.0.0.1, length 28
    20:38:04.638059 00:00:00:00:00:02 > 00:00:00:00:00:01, ethertype ARP (0x0806), length 42: Reply 10.0.0.2 is-at 00:00:00:00:00:02, length 28
    20:38:04.722601 00:00:00:00:00:01 > 00:00:00:00:00:02, ethertype IPv4 (0x0800), length 98: 10.0.0.1 > 10.0.0.2: ICMP echo request, id 3940, seq 1, length 64
    20:38:04.722747 00:00:00:00:00:02 > 00:00:00:00:00:01, ethertype IPv4 (0x0800), length 98: 10.0.0.2 > 10.0.0.1: ICMP echo reply, id 3940, seq 1, length 64


ホスト2では、ホスト1が発行したARP requestを受信し、ホスト1にARP replyを
返しています。続いて、ホスト1からのICMP echo requestを受信し、ホスト1に
echo replyを返しています。

host: h3:

.. rst-class:: console

::

    root@ryu-vm:~# tcpdump -en -i h3-eth0
    tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
    listening on h3-eth0, link-type EN10MB (Ethernet), capture size 65535 bytes
    20:38:04.637954 00:00:00:00:00:01 > ff:ff:ff:ff:ff:ff, ethertype ARP (0x0806), length 42: Request who-has 10.0.0.2 tell 10.0.0.1, length 28


ホスト3では、最初にホスト1がブロードキャストしたARP requestのみを受信
しています。



まとめ
------

本章では、簡単なスイッチングハブの実装を題材に、Ryuアプリケーションの実装
の基本的な手順と、OpenFlowによるOpenFlowスイッチの簡単な制御方法について
説明しました。

