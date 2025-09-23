1. 手动提取出每个章节的每个小节，用一个Json数据进行封装,作为语言大模型的输入
2. 将1.pdf\2.pdf...并行输入语言大模型 - 先把考试试题的数据解析出来：严格Prompt规定传出的数据是json格式{"id":"","title":{""},"type":"","answer":{""},"refer":""}，方便后续数据处理；其中id是index，title是题目，type是题型，answer是标准答案
3. 将每一个解析出来的试卷json数据进行Saprse,然后统一记录进一个csv表格中，表头："id","title","type","answer",
4. 统计可视化csv中的题型数据，找出哪些题型最常考，哪些知识点最常考

注意⚠️！使用的是google AI,https://aistudio.google.com/apikey,xxx,绑定在.env中放置泄漏，

1. Characterization of Distributed 
Systems & System Models
 What is a Distributed System (DS)?
 Fundamental characteristics of DS 
 Main motivation of DS – resource sharing (the 
Web example)
 What are the issues and problems in DS?
 Architecture models
 Fundamental models
 Summary
2. Interprocess Communication
 External Data Representation & Marshalling
 Client-Server Communication
 Summary
3. Distributed Objects 
& Remote Invocation
 Object-based model: remote method 
invocation (RMI)
 Distributed object model
 Architecture of RMI
 An example of Java RMI
 Summary
4. Distributed File Systems
 Introduction
 Sun Network File System
 Andrew and Coda File Systems
 Summary
5. Peer-to-Peer File Sharing Systems
 Introduction
 Unstructured P2P File Sharing
 Structured DHT Systems
 Summary
6. Name Services
 Names and Name Services
 Domain Name System
 Summary
7. Time and Global States
 Synchronizing Physical Clocks
 Causal Ordering and Logical Clocks
 Global States
 Distributed Debugging
 Summary