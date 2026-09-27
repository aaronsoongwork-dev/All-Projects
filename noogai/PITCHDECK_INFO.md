# **Pitch Deck Info**
## 1. **Project Overview**:
**Problem Statement**

NoogAI can analyse videos and their comments at scale in order to infer certain metrics from them. Metrics such as comment quality, relevance to the video, video spam rate, comment catagory (beauty related), video overall comment quality and more.

## 2. **Project Benefits**:
**Target Audience**
- Social media / content strategists - People who need actionable insights to optimize content, decide themes, and measure Share of Engagement (SOE) metrics
- Brand / marketing managers - People who want high-level KPIs (quality comment ratio, sentiment, catagory breakdown) to inform campaigns.
- Social media Influencers (beauty) / Agencies - People who need per-video analytics and catagory insights to optimize creator content.

**Advantages**
- Specifically targeting beauty products

## 3. **Project Deliverables**:
**Final Product**
- Dashboard - Streamlit powered dashboard showcaseing data insights gleamed from running the model on the video and comment dataset
- Python Model - Used to run all ETL steps on dataset to produce output
- Prototype Model - Jupyter notebook used for the creation of the python model, can be viewed for a easier to read step-by-step option
- Output CSV file - Data insights after being fully transformed

**Deployment**
- Deployment for **large** datasets (1 mil comments+) requires a sufficently powerful GPU to run the sentiment analysis model.
- Time estimations for running the model on 1 million comments is roughly 160 minutes (2 hrs 40 mins) - with a GTX1660 Super
- With translation enabled this shoots up substantially (code commented out)
- GPUs used for testing are the Nvidia GTX1660 Super and Nvidia T4 Tensor Core GPU (Google Colab Free Tier)

## 4. **Development Methodology**:
**Tools and Technologies**

Libraries used:
- pandas - dataframe library used to ogranize and transform data
- matplotlib - used to plot graphs with data
- plotly - used to plot graphs with data
- huggingface transformers - used to run pretrained model (sentiment analysis model)
- huggingface hub - used to download pretrained model
- scikit-learn - TfidfVectorizer used for relevance analysis
- streamlit - used for dashboard creation
- ntlk - used to preprocess data and stem words

Programming Language: python

Tools used:
- Jupyter notebook - used for prototyping and data engineering
- Google Cloud Storage Free Tier - used to host datasets (before and after analysis)
- Google Colab - used for testing and development
- Youtube Data API V3 - used to aquire video specific data for dashboard feature where you can enter a youtube link and analyse comments on said video

**Licensing and Costs**
1. Google Cloud Storage - Free Tier used
2. Google Colab - Free Tier used
3. Youtube Data API V3 - 10000 request daily free limit, exceeding this can incur costs

## 5. **Future Plans and Possibilities**:
**Expansion Possibilities**
- Given more time features such as classification based catagorization and comment translation can be added.
- Comment Translation time estimate:
  - Google Translate API: 5000 mins (83hr+) per 1 mil comments
  - BERT based pretrained transformer: 3000 mins (50 hrs) per 1 mil comments on a GTX1660 Super
- Given more time and GPU power it is possible to cut down on time
- Limitations for this project include:
  - GPU Power / Time: Google Colab has a 4 hr limit on GPU time for the free tier, which is insufficient for running significant operations on large datasets. Additionally GPU access is limited to the T4 GPU which may be insufficient for quicker opperations
  - Youtube API calls - Daily 10000 quota, 1 api call per 100 comments. If a video has 1000 comments it will take 10 API calls. Scaling up if a video has 1000000 comments it will take 10000 API calls, resulting in the daily quota being exaused on a single high performing video (thankfully only very few videos have above 1 mil comments notably the Rick Roll video at over 2 mil).

**Overcoming Limitations**
- A big thing that can be overcome given time and budget is the speed of processing, as that is solely limited by GPU power and availability as well as the method in which a dataset is fed to the model.
- More accurate predictions will also be possible with the budget to collect data regarding text catagorization, specifically for catagorization as there are scarcely any online datasets with beauty related texts with labels.