.. _ch_switch_test_tool:

OpenFlow 測試工具
=================

本章將說明如何驗證 OpenFlow 交換器支援的完整度，及測試工具的使用方法。

測試工具概要
------------------

本工具 flow entry 
本ツールは、テストパターンファイルに従って試験対象のOpenFlowスイッチに
対してフローエントリやメーターエントリの登録／パケット印加を実施し、
OpenFlowスイッチのパケット書き換えや転送(または破棄)の処理結果と、
テストパターンファイルに記述された「期待する処理結果」の比較を行うことにより、
OpenFlowスイッチのOpenFlow仕様への対応状況を検証するテストツールです。

測試工具中，已經支援 OpenFlow 1.3 版本的 FlowMod 訊息，MeterMod 訊息和 GroupMod 訊息的測試。


============================== ================================
測試訊息種類                     相對應參數
============================== ================================
OpenFlow1.3 FlowMod 訊息       match (IN_PHY_PORT 除外)

                               actions (SET_QUEUE 除外)

OpenFlow1.3 MeterMod 訊息       全部
OpenFlow1.3 GroupMod 訊息       全部
============================== ================================

若要對更詳細的資料關於封包的產生以及修改封包，請參考「 :ref:`ch_packet_lib` 」。


操作綱要
^^^^^^^^

驗證執行的環境圖
""""""""""""

測試工具實際執行時如下示意圖。測試範本檔案中包含了 “待加入的 flow entry和 meta entry“、”檢驗封包”和”預期處理結果”。為了執行測試執行所需的環境設定將在後面的 `ツール実行環境`_ 中描述。

.. only:: latex

    .. image:: images/switch_test_tool/fig1.eps
        :align: center

.. only:: epub

    .. image:: images/switch_test_tool/fig1.png
        :align: center

.. only:: not latex and not epub

    .. image:: images/switch_test_tool/fig1.png
        :scale: 60 %
        :align: center



輸出測試結果
""""""""""

指定測試範例檔案中的測試案例依序執行之後會顯示最終的結果(OK/ERROR)。在出現 ERROR 的測試項結果時，錯誤訊息會一併出現在畫面上，最後的測試結果會指出OK/ERROR的數量並將錯誤的內容輸出。

.. rst-class:: console

::

    --- Test start ---

    match: 29_ICMPV6_TYPE
        ethernet/ipv6/icmpv6(type=128)-->'icmpv6_type=128,actions=output:2'               OK
        ethernet/ipv6/icmpv6(type=128)-->'icmpv6_type=128,actions=output:CONTROLLER'      OK
        ethernet/ipv6/icmpv6(type=135)-->'icmpv6_type=128,actions=output:2'               OK
        ethernet/vlan/ipv6/icmpv6(type=128)-->'icmpv6_type=128,actions=output:2'          ERROR
            Received incorrect packet-in: ethernet(ethertype=34525)
        ethernet/vlan/ipv6/icmpv6(type=128)-->'icmpv6_type=128,actions=output:CONTROLLER' ERROR
            Received incorrect packet-in: ethernet(ethertype=34525)
    match: 30_ICMPV6_CODE
        ethernet/ipv6/icmpv6(code=0)-->'icmpv6_code=0,actions=output:2'                   OK
        ethernet/ipv6/icmpv6(code=0)-->'icmpv6_code=0,actions=output:CONTROLLER'          OK
        ethernet/ipv6/icmpv6(code=1)-->'icmpv6_code=0,actions=output:2'                   OK
        ethernet/vlan/ipv6/icmpv6(code=0)-->'icmpv6_code=0,actions=output:2'              ERROR
            Received incorrect packet-in: ethernet(ethertype=34525)
        ethernet/vlan/ipv6/icmpv6(code=0)-->'icmpv6_code=0,actions=output:CONTROLLER'     ERROR
            Received incorrect packet-in: ethernet(ethertype=34525)

    ---  Test end  ---

    --- Test report ---
    Received incorrect packet-in(4)
        match: 29_ICMPV6_TYPE                    ethernet/vlan/ipv6/icmpv6(type=128)-->'icmpv6_type=128,actions=output:2'
        match: 29_ICMPV6_TYPE                    ethernet/vlan/ipv6/icmpv6(type=128)-->'icmpv6_type=128,actions=output:CONTROLLER'
        match: 30_ICMPV6_CODE                    ethernet/vlan/ipv6/icmpv6(code=0)-->'icmpv6_code=0,actions=output:2'
        match: 30_ICMPV6_CODE                    ethernet/vlan/ipv6/icmpv6(code=0)-->'icmpv6_code=0,actions=output:CONTROLLER'

    OK(6) / ERROR(4)


使用方法
--------

下面說明如何使用測試工具。

測試範本檔案
^^^^^^^^^^^

你需要遵照測試範本的相關規範來建立一個測試範本以滿足你想要完成的測試項目。

測試範本的附檔名是「.json」，他的格式如下。

.. rst-class:: sourcecode

::

    [
        "xxxxxxxxxx",                    # 測試名稱
        {
            "description": "xxxxxxxxxx", # 測試內容的描述
            "prerequisite": [
                {
                    "OFPFlowMod": {...}  # 要登錄的 flow entry，meter entry，group entry
                },                       # (Ryu 的 OFPFlowMod、OFPMeterMod、OFPGroupMod 使用 json 的形態描述)
                {                        #
                    "OFPMeterMod": {...} # flow entry 預期處理結果
                },                       # 封包轉送的情況(actions=output)
                {                        # 轉送輸出封包的編號請指定為「2」
                    "OFPGroupMod": {...} # 封包轉送至 group entry 的情況
                },                       # 請指定埠號為「2」或「3」
                {...}                    # 
            ],
            "tests": [
                {
                    # 修改封包
                    # 1回だけ印加するのか一定時間連続して印加し続けるのかに応じて
                    # (A)(B)のいずれかを記述
                    #  (A) 1回だけ印加
                    "ingress": [
                        "ethernet(...)", # (Ryuパケットライブラリのコンストラクタの形式で記述)
                        "ipv4(...)",
                        "tcp(...)"
                    ],
                    #  (B) 一定時間連続して印加
                    "ingress": {
                        "packets":{
                            "data":[
                                "ethernet(...)", # (A)と同じ
                                "ipv4(...)",
                                "tcp(...)"
                            ],
                            "pktps": 1000,       # 毎秒印加するパケット数を指定
                            "duration_time": 30  # 連続印加時間を秒単位で指定
                        }
                    },

                    # 預期處理的結果
                    # 処理結果の種別に応じて(a)(b)(c)(d)のいずれかを記述
                    #  (a) パケット転送(actions=output:X)の確認試験
                    "egress": [          # 期待する転送パケット
                        "ethernet(...)",
                        "ipv4(...)",
                        "tcp(...)"
                    ]
                    #  (b) パケットイン(actions=CONTROLLER)の確認試験
                    "PACKET_IN": [       # 期待するPacket-Inデータ
                        "ethernet(...)",
                        "ipv4(...)",
                        "tcp(...)"
                    ]
                    #  (c) table-missの確認試験
                    "table-miss": [      # table-missとなることを期待するフローテーブルID
                        0
                    ]
                    #  (d) パケット転送(actions=output:X)時スループットの確認試験
                    "egress":[
                        "throughput":[
                            {
                                "OFPMatch":{   # スループット計測用に
                                  ...          # 補助SWに登録される
                                },             # フローエントリのMatch条件
                                "kbps":1000    # 期待するスループットをKbps単位で指定
                            },
                            {...},
                            {...}
                        ]
                    ]
                },
                {...},
                {...}
            ]
        },                               # 試験1
        {...},                           # 試験2
        {...}                            # 試験3
    ]

印加パケットとして「(B) 一定時間連続して印加」を、
期待する処理結果として「(d) パケット転送(actions=output:X)時スループットの確認試験」を
それぞれ記述することにより、試験対象SWのスループットを計測することができます。


.. NOTE::

    作為一個測試樣板範本，Ryu 的原始碼提供了樣板檔案來檢查測試是否符合 OpenFlow1.3 FlowMod 中 match/action 訊息的參數適不適合。

        ryu/tests/switch/of13


測試工具執行環境
^^^^^^^^^^^^^^

接下來說明測試工具執行時所需的環境


.. only:: latex

    .. image:: images/switch_test_tool/fig2.eps
        :align: center

.. only:: epub

    .. image:: images/switch_test_tool/fig2.png
        :align: center

.. only:: not latex and not epub

    .. image:: images/switch_test_tool/fig2.png
        :scale: 60 %
        :align: center

做為輔助交換器來說，下列的條件是一個 OpenFlow 交換器必須要支援的。

* actions=CONTROLLER flow entry 註冊

* 流量監控用的 flow entry 註冊

* 透過 flow entry 發送 Packet-In 訊息到 controller，actions=CONTROLLER 。

* 接受 Packet-Out 訊息並發送封包


.. NOTE::

    Ryu 原始碼當中利用腳本實作了一個在 mininet 上的測試環境，當中的待測交換器是 Open vSwtich。

        ryu/tests/switch/run_mininet.py

    腳本的使用範例請參照「 `テストツール使用例`_ 」。


測試工具的執行方法
^^^^^^^^^^^^^^^^^^^^^^

測試工具被公開在 Ryu 的原始碼當中。

    =============================== ===============================
    原始碼                           説明
    =============================== ===============================
    ryu/tests/switch/tester.py      測試工具
    ryu/tests/switch/of13           測試樣版的一些範例
    ryu/tests/switch/run_mininet.py 建立測試環境的腳本
    =============================== ===============================

使用接下來的指令執行測試工具。

.. rst-class:: console

::

    $ ryu-manager [--test-switch-target DPID] [--test-switch-tester DPID]
     [--test-switch-dir DIRECTORY] ryu/tests/switch/tester.py

..


    ==================== ======================================== =====================
    選項                  説明                                     預設值
    ==================== ======================================== =====================
    --test-switch-target 測試目的交換器的 datapath ID               0000000000000001
    --test-switch-tester 測試輔助交換器的 datapath ID               0000000000000002
    --test-switch-dir    測試樣板的存放路徑                          ryu/tests/switch/of13
    ==================== ======================================== =====================


.. NOTE::

    測試工具是繼承自 ryu.base.app_manager.RyuApp 的一個應用程式。跟其他的 Ryu 應用程式一樣使用
    --verbose 選項顯示除錯的訊息。


測試工具啟動之後，測試目的交換器和測試輔助交換器和 controller 進行連接，接著測試就會使用指定的測試樣板開始進行測試。

測試工具使用範例
------------------

下面介紹如何使用和測試樣板範例檔和原始測試樣板檔案的順序。


執行測試樣本檔案的順序
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

使用 Ryu 的原始碼中測試樣板範本 (ryu/tests/switch/of13) 來檢查 FlowMod訊息的 match/action，MeterMod的訊息和 GroupMod訊息

本程序中測試環境和測試環境的產生腳本(ryu/tests/switch/run_mininet.py)，也因此測試目標是 Open vSwitch。使用 VM image 來打造測試環境以及登入的方法請參照「 :ref:`ch_switching_hub` 」以取得更詳細的資料。

1. 建構測試環境

    VM環境的登入，執行測試環境的建構腳本。

    .. rst-class:: console

    ::

        ryu@ryu-vm:~$ sudo ryu/ryu/tests/switch/run_mininet.py


    net 命令的執行結果如下。

    .. rst-class:: console

    ::

        mininet> net
        c0
        s1 lo:  s1-eth1:s2-eth1 s1-eth2:s2-eth2 s1-eth3:s2-eth3
        s2 lo:  s2-eth1:s1-eth1 s2-eth2:s1-eth2 s2-eth3:s1-eth3



2. 測試工具的執行

    為了執行測試工具，打開連線到 controller 的 xterm。

    .. rst-class:: console

    ::

        mininet> xterm c0


    在「Node: c0 (root)」的 xterm 中啟動測試工具。
    這時候，做為測試樣本檔案的位置，請指定測試樣本範例路徑(ryu/tests/switch/of13)。
    接著，由於 mininet 測試環境中測試目標交換器和測試輔助交換器的 datapath ID 均有預設值，因此
    --test-switch-target／--test-switch-tester 選項可省略。

    Node: c0:

    .. rst-class:: console

    ::

        root@ryu-vm:~$ ryu-manager --test-switch-dir ryu/ryu/tests/switch/of13 ryu/ryu/tests/switch/tester.py


    測試工具執行之後就會出現下列訊息，並等待測試目標交換器和測試輔助交換器連結到 controller。

    .. rst-class:: console

    ::

        root@ryu-vm:~$ ryu-manager --test-switch-dir ryu/ryu/tests/switch/of13/ ryu/ryu/tests/switch/tester.py
        loading app ryu/ryu/tests/switch/tester.py
        loading app ryu.controller.ofp_handler
        instantiating app ryu/ryu/tests/switch/tester.py of OfTester
        target_dpid=0000000000000001
        tester_dpid=0000000000000002
        Test files directory = ryu/ryu/tests/switch/of13/
        instantiating app ryu.controller.ofp_handler of OFPHandler
        --- Test start ---
        waiting for switches connection...




    試験対象スイッチと補助スイッチがコントローラに接続されると、
    試験が開始されます。


    .. rst-class:: console

    ::

        root@ryu-vm:~$ ryu-manager --test-switch-dir ryu/ryu/tests/switch/of13/ ryu/ryu/tests/switch/tester.py
        loading app ryu/ryu/tests/switch/tester.py
        loading app ryu.controller.ofp_handler
        instantiating app ryu/ryu/tests/switch/tester.py of OfTester
        target_dpid=0000000000000001
        tester_dpid=0000000000000002
        Test files directory = ryu/ryu/tests/switch/of13/
        instantiating app ryu.controller.ofp_handler of OFPHandler
        --- Test start ---
        waiting for switches connection...
        dpid=0000000000000002 : Join tester SW.
        dpid=0000000000000001 : Join target SW.
        action: 00_OUTPUT
            ethernet/ipv4/tcp-->'actions=output:2'      OK
            ethernet/ipv6/tcp-->'actions=output:2'      OK
            ethernet/arp-->'actions=output:2'           OK
        action: 11_COPY_TTL_OUT
            ethernet/mpls(ttl=64)/ipv4(ttl=32)/tcp-->'eth_type=0x8847,actions=copy_ttl_out,output:2'        ERROR
                Failed to add flows: OFPErrorMsg[type=0x02, code=0x00]
            ethernet/mpls(ttl=64)/ipv6(hop_limit=32)/tcp-->'eth_type=0x8847,actions=copy_ttl_out,output:2'  ERROR
                Failed to add flows: OFPErrorMsg[type=0x02, code=0x00]
        ...


    ryu/tests/switch/of13配下の全てのサンプルテストパターンファイルの試験
    が完了すると、テストツールは終了します。


<参考>
""""""

    サンプルテストパターンファイル一覧

        match／actionsの各設定項目に対応するフローエントリを登録し、
        フローエントリにmatchする(またはmatchしない)複数パターンのパケット
        を印加するテストパターンや、一定頻度以上の印加に対して破棄もしくは
        優先度変更を行うメーターエントリを登録し、メーターエントリにmatch
        するパケットを連続的に印加するテストパターン、全ポートにFLOODINGする
        type=ALLのグループエントリや振り分け条件によって出力先ポートを自動的
        に変更するtype=SELECTのグループエントリを登録し、グループエントリに
        matchするパケットを連続的に印加するテストパターンが用意されています。


    .. rst-class:: console

    ::

        ryu/tests/switch/of13/action:
        00_OUTPUT.json              20_POP_MPLS.json
        11_COPY_TTL_OUT.json        23_SET_NW_TTL_IPv4.json
        12_COPY_TTL_IN.json         23_SET_NW_TTL_IPv6.json
        15_SET_MPLS_TTL.json        24_DEC_NW_TTL_IPv4.json
        16_DEC_MPLS_TTL.json        24_DEC_NW_TTL_IPv6.json
        17_PUSH_VLAN.json           25_SET_FIELD
        17_PUSH_VLAN_multiple.json  26_PUSH_PBB.json
        18_POP_VLAN.json            26_PUSH_PBB_multiple.json
        19_PUSH_MPLS.json           27_POP_PBB.json
        19_PUSH_MPLS_multiple.json

        ryu/tests/switch/of13/action/25_SET_FIELD:
        03_ETH_DST.json        14_TCP_DST_IPv4.json   24_ARP_SHA.json
        04_ETH_SRC.json        14_TCP_DST_IPv6.json   25_ARP_THA.json
        05_ETH_TYPE.json       15_UDP_SRC_IPv4.json   26_IPV6_SRC.json
        06_VLAN_VID.json       15_UDP_SRC_IPv6.json   27_IPV6_DST.json
        07_VLAN_PCP.json       16_UDP_DST_IPv4.json   28_IPV6_FLABEL.json
        08_IP_DSCP_IPv4.json   16_UDP_DST_IPv6.json   29_ICMPV6_TYPE.json
        08_IP_DSCP_IPv6.json   17_SCTP_SRC_IPv4.json  30_ICMPV6_CODE.json
        09_IP_ECN_IPv4.json    17_SCTP_SRC_IPv6.json  31_IPV6_ND_TARGET.json
        09_IP_ECN_IPv6.json    18_SCTP_DST_IPv4.json  32_IPV6_ND_SLL.json
        10_IP_PROTO_IPv4.json  18_SCTP_DST_IPv6.json  33_IPV6_ND_TLL.json
        10_IP_PROTO_IPv6.json  19_ICMPV4_TYPE.json    34_MPLS_LABEL.json
        11_IPV4_SRC.json       20_ICMPV4_CODE.json    35_MPLS_TC.json
        12_IPV4_DST.json       21_ARP_OP.json         36_MPLS_BOS.json
        13_TCP_SRC_IPv4.json   22_ARP_SPA.json        37_PBB_ISID.json
        13_TCP_SRC_IPv6.json   23_ARP_TPA.json        38_TUNNEL_ID.json

        ryu/tests/switch/of13/group:
        00_ALL.json           01_SELECT_IP.json            01_SELECT_Weight_IP.json
        01_SELECT_Ether.json  01_SELECT_Weight_Ether.json

        ryu/tests/switch/of13/match:
        00_IN_PORT.json        13_TCP_SRC_IPv4.json   25_ARP_THA.json
        02_METADATA.json       13_TCP_SRC_IPv6.json   25_ARP_THA_Mask.json
        02_METADATA_Mask.json  14_TCP_DST_IPv4.json   26_IPV6_SRC.json
        03_ETH_DST.json        14_TCP_DST_IPv6.json   26_IPV6_SRC_Mask.json
        03_ETH_DST_Mask.json   15_UDP_SRC_IPv4.json   27_IPV6_DST.json
        04_ETH_SRC.json        15_UDP_SRC_IPv6.json   27_IPV6_DST_Mask.json
        04_ETH_SRC_Mask.json   16_UDP_DST_IPv4.json   28_IPV6_FLABEL.json
        05_ETH_TYPE.json       16_UDP_DST_IPv6.json   29_ICMPV6_TYPE.json
        06_VLAN_VID.json       17_SCTP_SRC_IPv4.json  30_ICMPV6_CODE.json
        06_VLAN_VID_Mask.json  17_SCTP_SRC_IPv6.json  31_IPV6_ND_TARGET.json
        07_VLAN_PCP.json       18_SCTP_DST_IPv4.json  32_IPV6_ND_SLL.json
        08_IP_DSCP_IPv4.json   18_SCTP_DST_IPv6.json  33_IPV6_ND_TLL.json
        08_IP_DSCP_IPv6.json   19_ICMPV4_TYPE.json    34_MPLS_LABEL.json
        09_IP_ECN_IPv4.json    20_ICMPV4_CODE.json    35_MPLS_TC.json
        09_IP_ECN_IPv6.json    21_ARP_OP.json         36_MPLS_BOS.json
        10_IP_PROTO_IPv4.json  22_ARP_SPA.json        37_PBB_ISID.json
        10_IP_PROTO_IPv6.json  22_ARP_SPA_Mask.json   37_PBB_ISID_Mask.json
        11_IPV4_SRC.json       23_ARP_TPA.json        38_TUNNEL_ID.json
        11_IPV4_SRC_Mask.json  23_ARP_TPA_Mask.json   38_TUNNEL_ID_Mask.json
        12_IPV4_DST.json       24_ARP_SHA.json        39_IPV6_EXTHDR.json
        12_IPV4_DST_Mask.json  24_ARP_SHA_Mask.json   39_IPV6_EXTHDR_Mask.json

        ryu/tests/switch/of13/meter:
        01_DROP_00_KBPS_00_1M.json      02_DSCP_REMARK_00_KBPS_00_1M.json
        01_DROP_00_KBPS_01_10M.json     02_DSCP_REMARK_00_KBPS_01_10M.json
        01_DROP_00_KBPS_02_100M.json    02_DSCP_REMARK_00_KBPS_02_100M.json
        01_DROP_01_PKTPS_00_100.json    02_DSCP_REMARK_01_PKTPS_00_100.json
        01_DROP_01_PKTPS_01_1000.json   02_DSCP_REMARK_01_PKTPS_01_1000.json
        01_DROP_01_PKTPS_02_10000.json  02_DSCP_REMARK_01_PKTPS_02_10000.json


オリジナルテストパターンの実行手順
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

次に、オリジナルのテストパターンを作成してテストツールを実行する手順を示します。

例として、OpenFlowスイッチがルータ機能を実現するために必要なmatch／actionsを
処理する機能を備えているかを確認するテストパターンを作成します。


1．テストパターンファイル作成

    ルータがルーティングテーブルに従ってパケットを転送する機能を実現する
    以下のフローエントリが正しく動作するかを試験します。


    =================================== ==================================================
    match                               actions
    =================================== ==================================================
    宛先IPアドレス帯「192.168.30.0/24」 送信元MACアドレスを「aa:aa:aa:aa:aa:aa」に書き換え

                                        宛先MACアドレスを「bb:bb:bb:bb:bb:bb」に書き換え

                                        TTL減算

                                        パケット転送
    =================================== ==================================================


    このテストパターンを実行するテストパターンファイルを作成します。


ファイル名： ``sample_test_pattern.json``

.. rst-class:: sourcecode

::

    [
       "sample: Router test",
       {
           "description": "static routing table",
           "prerequisite": [
               {
                   "OFPFlowMod": {
                       "table_id": 0,
                       "match": {
                           "OFPMatch": {
                               "oxm_fields": [
                                   {
                                       "OXMTlv": {
                                           "field": "eth_type",
                                           "value": 2048
                                       }
                                   },
                                   {
                                       "OXMTlv": {
                                           "field": "ipv4_dst",
                                           "mask": 4294967040,
                                           "value": "192.168.30.0"
                                       }
                                   }
                              ]
                           }
                       },
                       "instructions":[
                           {
                               "OFPInstructionActions": {
                                   "actions":[
                                       {
                                           "OFPActionSetField":{
                                               "field":{
                                                   "OXMTlv":{
                                                       "field":"eth_src",
                                                       "value":"aa:aa:aa:aa:aa:aa"
                                                   }
                                               }
                                           }
                                       },
                                       {
                                           "OFPActionSetField":{
                                               "field":{
                                                   "OXMTlv":{
                                                       "field":"eth_dst",
                                                       "value":"bb:bb:bb:bb:bb:bb"
                                                   }
                                               }
                                           }
                                       },
                                       {
                                           "OFPActionDecNwTtl":{}
                                       },
                                       {
                                           "OFPActionOutput": {
                                               "port":2
                                           }
                                       }
                                   ],
                                   "type": 4
                               }
                           }
                       ]
                   }
               }
           ],
           "tests":[
               {
                   "ingress":[
                       "ethernet(dst='22:22:22:22:22:22',src='11:11:11:11:11:11',ethertype=2048)",
                       "ipv4(tos=32, proto=6, src='192.168.10.10', dst='192.168.30.10', ttl=64)",
                       "tcp(dst_port=2222, option='\\x00\\x00\\x00\\x00', src_port=11111)",
                       "'\\x01\\x02\\x03\\x04\\x05\\x06\\x07\\x08\\t\\n\\x0b\\x0c\\r\\x0e\\x0f'"
                   ],
                   "egress":[
                       "ethernet(dst='bb:bb:bb:bb:bb:bb',src='aa:aa:aa:aa:aa:aa',ethertype=2048)",
                       "ipv4(tos=32, proto=6, src='192.168.10.10', dst='192.168.30.10', ttl=63)",
                       "tcp(dst_port=2222, option='\\x00\\x00\\x00\\x00', src_port=11111)",
                       "'\\x01\\x02\\x03\\x04\\x05\\x06\\x07\\x08\\t\\n\\x0b\\x0c\\r\\x0e\\x0f'"
                   ]
               }
           ]
       }
    ]


2．試験環境構築

    試験環境構築スクリプトを用いて試験環境を構築します。手順は
    `サンプルテストパターンの実行手順`_ を参照してください。


3．テストツール実行

    コントローラのxtermから、先ほど作成したオリジナルのテストパターンファイル
    を指定してテストツールを実行します。
    なお、--test-switch-dirオプションはディレクトリだけでなくファイルを直接
    指定することも可能です。また、送受信パケットの内容を確認するため
    --verboseオプションを指定しています。


    Node: c0:

    .. rst-class:: console

    ::

        root@ryu-vm:~$ ryu-manager --verbose --test-switch-dir ./sample_test_pattern.json ryu/ryu/tests/switch/tester.py


    試験対象スイッチと補助スイッチがコントローラに接続されると、試験が
    開始されます。

    「dpid=0000000000000002 : receive_packet...」のログ出力から、テスト
    パターンファイルのegressパケットとして設定した、期待する出力パケット
    が送信されたことが分かります。
    なお、ここではテストツールが出力したログのみを抜粋しています。

    .. rst-class:: console

    ::

        root@ryu-vm:~$ ryu-manager --verbose --test-switch-dir ./sample_test_pattern.json ryu/ryu/tests/switch/tester.py
        loading app ryu/tests/switch/tester.py
        loading app ryu.controller.ofp_handler
        instantiating app ryu.controller.ofp_handler of OFPHandler
        instantiating app ryu/tests/switch/tester.py of OfTester
        target_dpid=0000000000000001
        tester_dpid=0000000000000002
        Test files directory = ./sample_test_pattern.json

        --- Test start ---
        waiting for switches connection...

        dpid=0000000000000002 : Join tester SW.
        dpid=0000000000000001 : Join target SW.

        sample: Router test

        send_packet:[ethernet(dst='22:22:22:22:22:22',ethertype=2048,src='11:11:11:11:11:11'), ipv4(csum=53560,dst='192.168.30.10',flags=0,header_length=5,identification=0,offset=0,option=None,proto=6,src='192.168.10.10',tos=32,total_length=59,ttl=64,version=4), tcp(ack=0,bits=0,csum=33311,dst_port=2222,offset=6,option='\x00\x00\x00\x00',seq=0,src_port=11111,urgent=0,window_size=0), '\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f']
        egress:[ethernet(dst='bb:bb:bb:bb:bb:bb',ethertype=2048,src='aa:aa:aa:aa:aa:aa'), ipv4(csum=53816,dst='192.168.30.10',flags=0,header_length=5,identification=0,offset=0,option=None,proto=6,src='192.168.10.10',tos=32,total_length=59,ttl=63,version=4), tcp(ack=0,bits=0,csum=33311,dst_port=2222,offset=6,option='\x00\x00\x00\x00',seq=0,src_port=11111,urgent=0,window_size=0), '\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f']
        packet_in:[]
        dpid=0000000000000002 : receive_packet[ethernet(dst='bb:bb:bb:bb:bb:bb',ethertype=2048,src='aa:aa:aa:aa:aa:aa'), ipv4(csum=53816,dst='192.168.30.10',flags=0,header_length=5,identification=0,offset=0,option=None,proto=6,src='192.168.10.10',tos=32,total_length=59,ttl=63,version=4), tcp(ack=0,bits=0,csum=33311,dst_port=2222,offset=6,option='\x00\x00\x00\x00',seq=0,src_port=11111,urgent=0,window_size=0), '\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f']
            static routing table                            OK
        ---  Test end  ---


    実際にOpenFlowスイッチに登録されたフローエントリは以下の通りです。
    テストツールによって印加されたパケットがフローエントリにmatchし、
    n_packetsがカウントアップされていることが分かります。


    Node: s1:

    .. rst-class:: console

    ::

        root@ryu-vm:~# ovs-ofctl -O OpenFlow13 dump-flows s1
        OFPST_FLOW reply (OF1.3) (xid=0x2):
         cookie=0x0, duration=56.217s, table=0, n_packets=1, n_bytes=73, priority=0,ip,nw_dst=192.168.30.0/24 actions=set_field:aa:aa:aa:aa:aa:aa->eth_src,set_field:bb:bb:bb:bb:bb:bb->eth_dst,dec_ttl,output:2


エラーメッセージ一覧
^^^^^^^^^^^^^^^^^^^^

本ツールで出力されるエラーメッセージの一覧を示します。

.. tabularcolumns:: |p{23zw}|p{23zw}|

======================================================================== ============================================================================================================
エラーメッセージ                                                         説明
======================================================================== ============================================================================================================
Failed to initialize flow tables: barrier request timeout.               前回試験の試験対象SW上のフローエントリ削除に失敗(Barrier Requestのタイムアウト)
Failed to initialize flow tables: [err_msg]                              前回試験の試験対象SW上のフローエントリ削除に失敗(FlowModに対するErrorメッセージ受信)
Failed to initialize flow tables of tester_sw: barrier request timeout.  前回試験の補助SW上のフローエントリ削除に失敗(Barrier Requestのタイムアウト)
Failed to initialize flow tables of tester_sw: [err_msg]                 前回試験の補助SW上のフローエントリ削除に失敗(FlowModに対するErrorメッセージ受信)
Failed to add flows: barrier request timeout.                            試験対象SWに対するフローエントリ登録に失敗(Barrier Requestのタイムアウト)
Failed to add flows: [err_msg]                                           試験対象SWに対するフローエントリ登録に失敗(FlowModに対するErrorメッセージ受信)
Failed to add flows to tester_sw: barrier request timeout.               補助SWに対するフローエントリ登録に失敗(Barrier Requestのタイムアウト)
Failed to add flows to tester_sw: [err_msg]                              補助SWに対するフローエントリ登録に失敗(FlowModに対するErrorメッセージ受信)
Failed to add meters: barrier request timeout.                           試験対象SWに対するメーターエントリ登録に失敗(Barrier Requestのタイムアウト)
Failed to add meters: [err_msg]                                          試験対象SWに対するメーターエントリ登録に失敗(MeterModに対するErrorメッセージ受信)
Failed to add groups: barrier request timeout.                           試験対象SWに対するグループエントリ登録に失敗(Barrier Requestのタイムアウト)
Failed to add groups: [err_msg]                                          試験対象SWに対するグループエントリ登録に失敗(GroupModに対するErrorメッセージ受信)
Added incorrect flows: [flows]                                           試験対象SWに対するフローエントリ登録確認エラー(想定外のフローエントリが登録された)
Failed to add flows: flow stats request timeout.                         試験対象SWに対するフローエントリ登録確認に失敗(FlowStats Requestのタイムアウト)
Failed to add flows: [err_msg]                                           試験対象SWに対するフローエントリ登録確認に失敗(FlowStats Requestに対するErrorメッセージ受信)
Added incorrect meters: [meters]                                         試験対象SWに対するメーターエントリ登録確認エラー(想定外のメーターエントリが登録された)
Failed to add meters: meter config stats request timeout.                試験対象SWに対するメーターエントリ登録確認に失敗(MeterConfigStats Requestのタイムアウト)
Failed to add meters: [err_msg]                                          試験対象SWに対するメーターエントリ登録確認に失敗(MeterConfigStats Requestに対するErrorメッセージ受信)
Added incorrect groups: [groups]                                         試験対象SWに対するグループエントリ登録確認エラー(想定外のグループエントリが登録された)
Failed to add groups: group desc stats request timeout.                  試験対象SWに対するグループエントリ登録確認に失敗(GroupDescStats Requestのタイムアウト)
Failed to add groups: [err_msg]                                          試験対象SWに対するグループエントリ登録確認に失敗(GroupDescStats Requestに対するErrorメッセージ受信)
Failed to request port stats from target: request timeout.               試験対象SWのPortStats取得に失敗(PortStats Requestのタイムアウト)
Failed to request port stats from target: [err_msg]                      試験対象SWのPortStats取得に失敗(PortStats Requestに対するErrorメッセージ受信)
Failed to request port stats from tester: request timeout.               補助SWのPortStats取得に失敗(PortStats Requestのタイムアウト)
Failed to request port stats from tester: [err_msg]                      補助SWのPortStats取得に失敗(PortStats Requestに対するErrorメッセージ受信)
Received incorrect [packet]                                              期待した出力パケットの受信エラー(異なるパケットを受信)
Receiving timeout: [detail]                                              期待した出力パケットの受信に失敗(タイムアウト)
Faild to send packet: barrier request timeout.                           パケット印加に失敗(Barrier Requestのタイムアウト)
Faild to send packet: [err_msg]                                          パケット印加に失敗(Packet-Outに対するErrorメッセージ受信)
Table-miss error: increment in matched_count.                            table-miss確認エラー(フローにmatchしている)
Table-miss error: no change in lookup_count.                             table-miss確認エラー(パケットが確認対象のフローテーブルで処理されていない)
Failed to request table stats: request timeout.                          table-missの確認に失敗(TableStats Requestのタイムアウト)
Failed to request table stats: [err_msg]                                 table-missの確認に失敗(TableStats Requestに対するErrorメッセージ受信)
Added incorrect flows to tester_sw: [flows]                              補助SWに対するフローエントリ登録確認エラー(想定外のフローエントリが登録された)
Failed to add flows to tester_sw: flow stats request timeout.            補助SWに対するフローエントリ登録確認に失敗(FlowStats Requestのタイムアウト)
Failed to add flows to tester_sw: [err_msg]                              補助SWに対するフローエントリ登録確認に失敗(FlowStats Requestに対するErrorメッセージ受信)
Failed to request flow stats: request timeout.                           スループット確認時、補助SWに対するフローエントリ登録確認に失敗(FlowStats Requestのタイムアウト)
Failed to request flow stats: [err_msg]                                  スループット確認時、補助SWに対するフローエントリ登録確認に失敗(FlowStats Requestに対するErrorメッセージ受信)
Received unexpected throughput: [detail]                                 想定するスループットからかけ離れたスループットを計測
Disconnected from switch                                                 試験対象SWもしくは補助SWからのリンク断発生
======================================================================== ============================================================================================================
