import pandas as pd
import utils
import settings.config as config


def load_narrative_data():
    """
    Loads in narrative data to generate mean embeddings for each.
    """
    data_path = config.CENTROID_STOR_PATH / config.CENTROID_FILENAME

    df_narr = pd.read_json(
        f'{data_path}',
        orient='split',
        dtype={'id': str}
    )

    # column with text pre-processing applied to tweet
    df_narr['normalized_tweet'] = df_narr['tweet'].apply(
        lambda tweet: utils.normalize_tweet(tweet)
    ).str.lower()

    return df_narr


def gen_embeds_narrative_df(tweet_embeddings, df):
    """
    Given embedding values and the original pandas Dataframe of the various
    narrative tweets, generates a pandas DataFrame that contains the embedding
    values for each tweet and their associated narrative.
    """
    tweet_embeddings_df = pd.DataFrame(tweet_embeddings)
    # change the column names to make them easier to slice
    tweet_embeddings_df.columns = [
        str(col) + '_embed' for col in tweet_embeddings_df.columns
    ]
    # add narrative for each embedding
    tweet_embed_with_narrative = pd.concat(
        [df['narrative'], pd.DataFrame(tweet_embeddings_df)],
        axis=1
    )
    return tweet_embed_with_narrative


def generate_mean_embeddings(model, df, column_name='normalized_tweet'):
    '''
    Given a SentenceTransformer model, a pandas DataFrame, and a column name
    (whose default value will take 'bert_tweet'), we'll encode a set of
    (unnormalized) embeddings on tweet text within the dataframe and return
    a dataframe with the mean embeddings for each narrative
    '''
    tweets = df[column_name]
    # generate embeddings with model
    tweet_embeddings = model.encode(tweets, show_progress_bar=True)
    # create dataframe of tweet embeddings
    tweet_embeddings_df = gen_embeds_narrative_df(tweet_embeddings, df)
    # group by narrative and then take mean embedding
    mean_narratives = tweet_embeddings_df.groupby('narrative').mean().reset_index(drop=False)
    # group by narrative and then return the standard deviation
    std_narratives = tweet_embeddings_df.groupby('narrative').std().reset_index(drop=False)
    # assert len(mean_narratives.index) == 20
    # assert len(std_narratives.index) == 20

    return mean_narratives, std_narratives


def main():
    """
    Main application: generates mean embeddings for misinformation narratives
    """
    utils.set_seed(config.SEED_VALUE)

    file_check = config.NARR_STORAGE_PATH / config.MEAN_NARR_FILENAME

    if file_check.is_file():
        print(f'Skipping the embedding generation step because {file_check} already exists.\n')
    else:
        print('Generating CSV files for mean and st. dev. of narrative embeddings...\n')
        df_narr = load_narrative_data()
        model = utils.create_embedding_model()

        mean_narratives, std_narratives = generate_mean_embeddings(
            model,
            df_narr
        )

        mean_narratives.to_csv(
            f'{config.NARR_STORAGE_PATH}/{config.MEAN_NARR_FILENAME}',
            index=False
        )

        std_narratives.to_csv(
            f'{config.NARR_STORAGE_PATH}/{config.STD_NARR_FILENAME}',
            index=False
        )

        print(
            '\nSaved the mean narrative embeddings, in addition to their standard deviations.\n',
            'Files are located at:\n\n'
            f'MEAN: {config.NARR_STORAGE_PATH}/{config.MEAN_NARR_FILENAME}', '\n',
            f'STDEV: {config.NARR_STORAGE_PATH}/{config.STD_NARR_FILENAME}', '\n'
        )


if __name__ == "__main__":
    main()
