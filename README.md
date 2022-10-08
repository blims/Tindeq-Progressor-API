# Tindeq-Progressor-API

This page describes the Progressor’s Bluetooth interface and is intended for users who want to develop a custom application for their device. The description assumes a basic understanding of the Bluetooth LE protocol.

The Progressor, with its Bluetooth 5 connectivity, can connect with most modern PCs or smartphones. Once a connection is established, the client application can control the Progressor’s operation through the commands specified here.

Bluetooth Services
The Progressor includes two Bluetooth services, one custom “Progressor” service which exposes the Progressors control interface, and the second one is the Nordic device firmware update (DFU) service. The DFU service will, however, not be covered here as it only accepts updates signed by Tindeq.
