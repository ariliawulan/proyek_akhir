import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
sns.set(style='dark')

# helper function untuk menghitung rata-rata ulasan berdasarkan kategori produk
def create_avg_review_per_category(df):
    avg_review_per_category = df.groupby('product_category_name_english')['review_score'].mean().reset_index()
    avg_review_per_category = avg_review_per_category.sort_values(by='review_score', ascending=False)
    avg_review_per_category.rename(columns={'review_score': 'average_review_score'}, inplace=True)
    
    return avg_review_per_category

# helper function untuk menghitung rata-rata waktu pengiriman
def create_avg_delivery_time(df):
    df['delivery_time_days'] = (df['order_delivered_customer_date'] - df['order_purchase_timestamp']).dt.days
    df_filtered = df[(df['delivery_time_days'] >= 0) & (df['delivery_time_days'] <= 90)]
    avg_delivery_time = df_filtered['delivery_time_days'].mean()
    return avg_delivery_time

# helper function untuk menghitung pelanggan yang paling aktif memberikan ulasan
def create_most_active_customers(order_ids, customer_ids, review_ids):
    # menggabungkan data order_id, customer_id, dan review_id menjadi satu DataFrame
    data = pd.DataFrame({
        'order_id': order_ids,
        'customer_id': customer_ids,
        'review_id': review_ids
    })
    # menghitung jumlah ulasan yang diberikan oleh setiap pelanggan
    active_customers_df = data.groupby('customer_id')['review_id'].count().reset_index()
    active_customers_df = active_customers_df.sort_values(by='review_id', ascending=False)
    active_customers_df.rename(columns={'review_id': 'review_count'}, inplace=True)
    
    return active_customers_df


# helper function untuk melakukan RFM analysis
def create_rfm_df(df):
    rfm_df = df.groupby('customer_id', as_index=False).agg({
        'order_purchase_timestamp': 'max',  
        'order_id': 'nunique',              
        'payment_value': 'sum'              
    })
    rfm_df.columns = ['customer_id', 'last_purchase', 'frequency', 'monetary']
    recent_date = df['order_purchase_timestamp'].max()
    rfm_df['recency'] = (recent_date - rfm_df['last_purchase']).dt.days
    rfm_df.drop('last_purchase', axis=1, inplace=True)
    return rfm_df

# Menggunakan path relatif ke file CSV yang berada dalam satu folder dengan dashboard.py
all_df = pd.read_csv('dashboard/all_data_new.csv')

# helper function untuk konversi datetime
datetime_columns = ['order_purchase_timestamp', 'order_delivered_customer_date']
all_df.sort_values(by='order_purchase_timestamp', inplace=True)
all_df.reset_index(inplace=True)

for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])

# Membuat komponen filter
min_date = all_df['order_purchase_timestamp'].min()
max_date = all_df['order_purchase_timestamp'].max()

with st.sidebar:
    st.image("https://github.com/dicodingacademy/assets/raw/main/logo.png")
    start_date, end_date = st.date_input(
        label='Rentang Waktu', min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

# Filter all_df berdasarkan rentang tanggal
main_df = all_df[(all_df["order_purchase_timestamp"] >= str(start_date)) & 
                (all_df["order_purchase_timestamp"] <= str(end_date))]

# Menghasilkan berbagai DataFrame dari helper functions
avg_review_per_category_df = create_avg_review_per_category(main_df)
avg_delivery_time = create_avg_delivery_time(main_df)

# Mendapatkan kolom untuk most_active_customers
order_ids = main_df['order_id']
customer_ids = main_df['customer_id']
review_ids = main_df['review_score']  # Atau kolom 'review_id' jika tersedia

most_active_customers_df = create_most_active_customers(order_ids, customer_ids, review_ids)

rfm_df = create_rfm_df(main_df)

# MELENGKAPI DASHBOARD DENGAN BERBAGAI VISUALISASI DATA

# Header
st.header('Dashboard Penjualan :sparkles:')

# Menampilkan rata-rata waktu pengiriman
st.subheader('Average Delivery Time')
st.metric(label="Average Delivery Time (Days)", value=round(avg_delivery_time, 2))

# Menampilkan rata-rata ulasan berdasarkan kategori produk
st.subheader('Reviews by Product Category')
fig, ax = plt.subplots(figsize=(12, 16))
sns.barplot(x='average_review_score', y='product_category_name_english', data=avg_review_per_category_df, ax=ax)
ax.set_xlabel("Average Review Score")
ax.set_ylabel("Product Category")
ax.set_title("Average Review Score by Product Category")
st.pyplot(fig)

# Menampilkan pelanggan yang paling aktif memberikan ulasan
st.subheader('The Most Active Customers Leave Reviews')
fig, ax = plt.subplots(figsize=(10, 6))
sns.barplot(x='review_count', y='customer_id', data=most_active_customers_df.head(10), ax=ax)
ax.set_xlabel("Review Count")
ax.set_ylabel("Customer ID")
ax.set_title("Top 10 Most Active Customers by Review Count")
st.pyplot(fig)

# Menampilkan parameter RFM
st.subheader("Best Customer Based on RFM Parameters")

# membuat 3 kolom untuk menampilkan metrik Recency, Frequency, dan Monetary
col1, col2, col3 = st.columns(3)

# menampilkan rata-rata Recency, Frequency, dan Monetary di kolom masing-masing
with col1:
    avg_recency = round(rfm_df['recency'].mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)

with col2:
    avg_frequency = round(rfm_df['frequency'].mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_monetary = format_currency(rfm_df['monetary'].mean(), "AUD", locale='es_CO')
    st.metric("Average Monetary", value=avg_monetary)

# Membuat visualisasi untuk Recency, Frequency, dan Monetary dalam 3 kolom
fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))
colors = ["#90CAF9"] * 5

# Bar plot for Recency
sns.barplot(y="recency", x="customer_id", data=rfm_df.sort_values(by="recency", ascending=True).head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel(None)
ax[0].set_title("By Recency (days)", loc="center", fontsize=18)
ax[0].tick_params(axis='x', labelsize=15, rotation=45)

# Bar plot for Frequency
sns.barplot(y="frequency", x="customer_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel(None)
ax[1].set_title("By Frequency", loc="center", fontsize=18)
ax[1].tick_params(axis='x', labelsize=15, rotation=45)

# Bar plot for Monetary
sns.barplot(y="monetary", x="customer_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
ax[2].set_ylabel(None)
ax[2].set_xlabel(None)
ax[2].set_title("By Monetary", loc="center", fontsize=18)
ax[2].tick_params(axis='x', labelsize=15, rotation=45)

st.pyplot(fig)
