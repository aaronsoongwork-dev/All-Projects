import pandas as pd


class Dataset:
    comment_links = [
        "https://storage.googleapis.com/dataset_hosting/comments1.csv",
        "https://storage.googleapis.com/dataset_hosting/comments2.csv",
        "https://storage.googleapis.com/dataset_hosting/comments3.csv",
        "https://storage.googleapis.com/dataset_hosting/comments4.csv",
        "https://storage.googleapis.com/dataset_hosting/comments5.csv",
    ]

    video_link = "https://storage.googleapis.com/dataset_hosting/videos.csv"

    @staticmethod
    def getAllComments():
        list_of_dfs = []
        for csv_file in Dataset.comment_links:
            df = pd.read_csv(csv_file)
            list_of_dfs.append(df)
        return pd.concat(list_of_dfs, ignore_index=True)

    @staticmethod
    def getComments(dataset_id=1, sample_frac=0.1):
        if dataset_id not in range(1, len(Dataset.comment_links) + 1):
            raise ValueError(f"dataset_id must be between 1 and {len(Dataset.comment_links)}")

        df = pd.read_csv(Dataset.comment_links[dataset_id - 1])
        if sample_frac < 1.0:
            df = df.sample(frac=sample_frac, random_state=42)
        return df

    @staticmethod
    def getVideos():
        return pd.read_csv(Dataset.video_link)


# Initialize dataset
dataset = Dataset()
print("Dataset class initialized successfully!")