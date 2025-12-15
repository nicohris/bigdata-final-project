

# 🚀📊 Social Media Monitoring System

## 🔥 Real-Time Big Data Pipeline for Brand Reputation Analysis

🎓 **Final Project — Big Data Introduction Course**
🛠️ **Option A: Technical Project**


## 🌟 Project Overview

This project showcases a **real-time Big Data pipeline** designed to monitor brand reputation on social media platforms.

By simulating Twitter activity, the system performs **sentiment analysis in real time**, stores large volumes of data efficiently, and provides **interactive dashboards** for instant insights.

Through this project, we demonstrate:

* Installation and configuration of Big Data tools
* Real-time data ingestion and processing
* Integration of multiple components into a unified architecture
* Practical problem-solving in a distributed environment

---

## 🏢 Business Use Case

**Company:** TechnoGadget Inc.
**Product:** #TechnoPhone

TechnoGadget Inc. wants to understand how customers perceive its new smartphone on social media.

**Key objectives:**

* Track overall customer sentiment (positive / negative / neutral)
* Detect complaint spikes as early as possible
* Identify trending hashtags and discussion topics
* Support customer service teams with actionable insights

---

## 🚫 Twitter API Limitation & Design Choice

The official Twitter (X) API is no longer freely accessible and requires expensive paid plans.

To keep the project **fully reproducible, free, and testable**, a **Tweet Simulator** was implemented.

The Tweet Simulator:

* Generates realistic brand-related tweets
* Simulates users, hashtags, follower counts, and timestamps
* Produces balanced positive, negative, and neutral sentiments
* Assigns unique tweet IDs to prevent duplicates
* Sends data continuously in real time

This approach allows us to demonstrate **real Big Data concepts** without relying on external services.

---

## 🏗️ System Architecture

Tweet Simulator
➡️ Kafka (real-time stream buffering)
➡️ ElasticSearch (indexed, scalable storage)
➡️ Kibana (interactive dashboards & analytics)

**Data flow:**

1. Tweets are generated and analyzed for sentiment
2. Kafka buffers and decouples the data stream
3. ElasticSearch indexes and stores tweets instantly
4. Kibana visualizes trends, sentiment, and volume in real time

---

## 🧰 Technology Stack

* **Message Broker:** Apache Kafka 7.5.0
* **Coordination Service:** Zookeeper 7.5.0
* **Storage & Search Engine:** ElasticSearch 8.11.0
* **Visualization Platform:** Kibana 8.11.0
* **Processing (optional):** Apache Spark 3.5.0
* **Sentiment Analysis:** TextBlob 0.17.1
* **Programming Language:** Python 3.10+
* **Containerization:** Docker

Apache Spark is included for experimentation only and is not required for the core pipeline.

---

## ⚙️ Installation & Execution

**Prerequisites:**

* Docker Desktop
* Python 3.10+
* pip

**Installation steps:**

Install Python dependencies
pip install -r requirements.txt

Start Docker services
docker-compose up -d

Launch the complete pipeline
start_pipeline.bat

**Kibana Dashboard:**
[http://localhost:5601](http://localhost:5601)

---

## 🧪 Minimal Working Example

The minimal working example demonstrates a full Big Data pipeline:

* Tweet generation
* Sentiment analysis
* Data ingestion and indexing
* Real-time visualization

**Example stored tweet:**

tweet_id: 17340129515234561234
sentiment_label: positive
sentiment_score: 0.65
hashtags: technophone
author_username: tech_lover_92
created_at: 2024-12-15T15:00:00Z

---

## 🌍 Big Data Ecosystem Integration

This project reflects a standard Big Data architecture:

* Ingestion layer: Kafka decouples producers and consumers
* Processing layer: real-time sentiment analysis
* Storage layer: ElasticSearch provides scalable indexed storage
* Analytics layer: Kibana enables real-time monitoring

The architecture can easily be extended with Spark or Hadoop for larger-scale processing.

---

## 🧠 My Setup Notes — Learning Experience

**Main challenge:** managing service startup dependencies in Docker.

**Problem encountered:**
The Tweet Simulator occasionally failed with a connection refused error on localhost:9200.

**Root cause:**
ElasticSearch requires significantly more startup time than Kafka or Zookeeper.

**Solution implemented:**

* Added a waiting mechanism in the startup script
* Checked ElasticSearch availability before sending data
* Delayed tweet generation until all services were ready

**What we learned:**

* Big Data services start at different speeds
* Orchestration is critical in distributed systems
* Reliable startup scripts are essential in real-world pipelines

---

## 📁 Project Structure

BigDataProject

* docker-compose.yml
* requirements.txt
* start_pipeline.bat
* stop_pipeline.bat
* src

  * ingestion
  * processing
  * utils
* data
* screens
* scripts

---

## 🖼️ Execution Proof

The `screens` directory contains screenshots showing:

* Running Docker containers
* Tweet generation logs
* Indexed data in ElasticSearch
* Real-time Kibana dashboards

These screenshots prove the correct execution of the pipeline.

---

## 🏁 Conclusion

This project demonstrates a **complete, functional, and realistic Big Data pipeline**, from data ingestion to real-time visualization.
It highlights both technical implementation and the practical challenges of working with distributed systems.

---

## 👥 Authors

Big Data Introduction Course — Final Project
Group of 2 students

Rihana Nicolas
Goudedranche Antoine

---

## 🙏 Acknowledgments

Apache Kafka
Elastic Stack
TextBlob
Docker

---
