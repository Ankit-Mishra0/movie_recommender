from pyspark.sql import SparkSession
from pyspark.sql.functions import explode, split, col
import matplotlib.pyplot as plt
import os

if not os.path.exists("visualizations"):
    os.makedirs("visualizations")


spark = SparkSession.builder.appName("Netflix Data Analyzer").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")


df = spark.read.option("header", True) \
    .option("inferSchema", True) \
    .csv("datasets/netflix_titles.csv")

print("Dataset Preview")
df.show(5)


type_df = df.filter(
    (col("type") == "Movie") | (col("type") == "TV Show")
)

type_count = type_df.groupBy("type").count()

type_pd = type_count.toPandas()
type_pd = type_pd.dropna()

plt.figure()
plt.bar(type_pd["type"].astype(str), type_pd["count"])

plt.title("Movies vs TV Shows")
plt.xlabel("Type")
plt.ylabel("Count")

plt.tight_layout()
plt.savefig("visualizations/type_distribution.png")
plt.close()

print("Saved: type_distribution.png")


year_growth = df.groupBy("release_year").count().orderBy("release_year")

year_pd = year_growth.toPandas()
year_pd = year_pd.dropna()

plt.figure()

plt.plot(year_pd["release_year"], year_pd["count"])

plt.title("Netflix Content Growth Per Year")
plt.xlabel("Release Year")
plt.ylabel("Number of Titles")

plt.tight_layout()
plt.savefig("visualizations/content_growth.png")
plt.close()

print("Saved: content_growth.png")


genres = df.withColumn(
    "genre",
    explode(split(col("listed_in"), ", "))
)

genre_count = genres.groupBy("genre") \
    .count() \
    .orderBy(col("count").desc())

genre_pd = genre_count.limit(10).toPandas()
genre_pd = genre_pd.dropna()

plt.figure()

plt.barh(genre_pd["genre"].astype(str), genre_pd["count"])

plt.title("Top 10 Netflix Genres")
plt.xlabel("Count")
plt.ylabel("Genre")

plt.gca().invert_yaxis()

plt.tight_layout()
plt.savefig("visualizations/top_genres.png")
plt.close()

print("Saved: top_genres.png")


country_count = df.groupBy("country") \
    .count() \
    .orderBy(col("count").desc())

country_pd = country_count.limit(10).toPandas()
country_pd = country_pd.dropna()

plt.figure()

plt.barh(country_pd["country"].astype(str), country_pd["count"])

plt.title("Top Countries Producing Netflix Content")
plt.xlabel("Number of Titles")
plt.ylabel("Country")

plt.gca().invert_yaxis()

plt.tight_layout()
plt.savefig("visualizations/top_countries.png")
plt.close()

print("Saved: top_countries.png")


spark.stop()

print("\nNetflix Data Analysis Completed Successfully!")
print("Check the 'visualizations' folder for generated charts.")