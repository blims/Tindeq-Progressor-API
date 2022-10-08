# Tindeq-Progressor-API

This page describes the Progressor’s Bluetooth interface and is intended for users who want to develop a custom application for their device. The description assumes a basic understanding of the Bluetooth LE protocol.

The Progressor, with its Bluetooth 5 connectivity, can connect with most modern PCs or smartphones. Once a connection is established, the client application can control the Progressor’s operation through the commands specified here.

Bluetooth Services
The Progressor includes two Bluetooth services, one custom “Progressor” service which exposes the Progressors control interface, and the second one is the Nordic device firmware update (DFU) service. The DFU service will, however, not be covered here as it only accepts updates signed by Tindeq.

![API-Figure1](https://user-images.githubusercontent.com/61838799/194727848-1470d918-61ae-4f8e-9a3c-f17c3a7c38d0.png)

**Control Point**

The control point characteristic is where we send commands to the Progressor. Each command is encoded into a tag-length-value (TLV) type of format as shown in Figure 2.
![API-Figure2](https://user-images.githubusercontent.com/61838799/194727891-619b6e28-5df4-42a7-8ce0-eecf364ef484.png)
![API-Table1](https://user-images.githubusercontent.com/61838799/194727896-de35097c-effe-4ed6-a64b-023ed8166994.png)

**Data Point**

The data point characteristic is where we receive data from the Progressor. The data is encoded into the same type of TLV format used for sending commands. Note: to receive data, the client must enable notifications for this characteristic first.

![API-Figure3](https://user-images.githubusercontent.com/61838799/194727955-0327cad9-9022-48ea-8a2b-080e36001089.png)
![API-Table2](https://user-images.githubusercontent.com/61838799/194727958-00b9eaf9-b012-4e69-89c5-75fff8ce6d88.png)


**Test tools**

nRF Connect for mobile is a generic Bluetooth developer app available for both Android and iOS. It is a convenient tool for inspecting and interacting with services and characteristics on Bluetooth LE enabled devices and can also be used for test and verification of the Progressor.

**Other notes**

As a part of its low power design, the Progressor features an auto-shutdown mechanism that will power off the device after 10 minutes of inactivity (i.e., when it is in a non-connected state). This means the Progressor will have to be turned on again if the shutdown timer is allowed to expire.
Data types received over Bluetooth are little endian. That is, the least significant byte is always received first.

**Python Example code**

Download a sample script for interfacing with the Progressor via Python here
