import streamlit as st
import pandas as pd 
import matplotlib.pyplot as plt
import json
import math

st.set_page_config(page_title='Review analyzer', layout='wide')

st.title("Product review analyzer")

if "df" not in st.session_state:
    st.session_state["df"] = None
if "category" not in st.session_state:
    st.session_state["category"] = None
if "aspects" not in st.session_state:
    st.session_state["aspects"] = None
if "expand" not in st.session_state:
    st.session_state["expand"] = True
if "all_product_meta" not in st.session_state:
    with open("product_meta.json", 'r') as fp:
        product_meta = json.load(fp)
    st.session_state["all_product_meta"] = product_meta
if "product_meta" not in st.session_state:
    st.session_state["product_meta"] = None
    
def product_info_mapper(product_name):
    st.session_state["product_meta"] = [p for p in st.session_state['all_product_meta'] if p['product_title'] ==  product_name][0]
    with open('category_aspects.json', 'r') as fp:
        data = json.load(fp)
    st.session_state["aspects"] = list(data[st.session_state["product_meta"]["product_category"]].keys())
        
def decide_colors(metrics):
    color_map = {
        'NEGATIVE': '#FF5741', 
        'NEUTRAL': '#FFDB2C', 
        'MOT MENTIONED': '#b066fa', 
        'POSITIVE': '#00946A'} 
    colors = [color_map[t] for t in metrics.keys()]
    return colors
    
def clean_display_review(text, max_window = 250):
    if type(text) == str:
        pass
    elif math.isnan(text):
        return text
    
    # if len(text) > 350:
    #     return text[:int(1.5*max_window)] + ("....." if len(text)>375 else "")
    if len(text) > max_window:
        return text[:max_window] + "....."
    else:
        return text

def clean_dsiplay_names(text):
    l_text = text.title().split("_")
    return " ".join(l_text)

def sort_dict(d):
    key = list(d.keys())
    key.sort()
    sorted_dict = {k: d[k] for k in key}
    return sorted_dict

def map_score_to_labels(metrics:dict):
    '''
    Map the 1.0, 0.0 and -1.0 to positive, neg and neutral.
    Also show percentage in (paranthesis)
    '''
    labels = []
    total_reviews = sum(metrics.values())
    # print(metrics)
    for k, v in metrics.items():
        try:
            label = str(k) + f": {str(100*v/total_reviews)[:4]}%"
        except:
            label = str(k) + f"-star : {str(100*v/total_reviews)[:4]}%"
        labels.append(label)
        
    return labels

def compute_aspect_metrics(col_name, keep_not_mentioned=True):   
    if col_name == 'review_rating':
        column = st.session_state["df"][col_name]    
    else:
        if keep_not_mentioned:
            column = st.session_state["df"][col_name]
        else:
            column = st.session_state["df"][col_name][st.session_state["df"][col_name] != 'NOT MENTIONED']
            
    column = dict(column.value_counts())
    return sort_dict(column)
    # return dict(column.value_counts(dropna=False))        # To show the 'nan' field counts too(will be seen in pie chart - ugly)

def display_sample_reviews(c, aspect, sentiment, count=5, expand=False, opinion=False):
    subset = st.session_state["df"][(len(st.session_state["df"]["review_content"]) > 50)&(st.session_state["df"][aspect] == sentiment)]
    if sentiment == 'POSITIVE':
        subset.sort_values(by='review_rating', ascending=False, inplace=True)
    if sentiment == 'NEGATIVE':
        subset.sort_values(by='review_rating', ascending=True, inplace=True)
    
    # String len condition
    subset = [row for i,row in subset.iterrows() if len(row['review_content'])>50]
    with c:
        for row in subset[:count]:
            c = st.container(border=True)
            if sentiment == "NEGATIVE":
                c.error(clean_display_review(row['review_content']))
                # c.error(row['review_content'])
            if sentiment == "POSITIVE":
                c.success(clean_display_review(row['review_content']))
                # c.success(row['review_content'])
            if opinion:
                c.warning(clean_display_review(row[str(aspect)+"_opinion"]))
                # c.warning(row[str(aspect)+"_opinion"])
  
def display_overview():
    cols = st.columns([10, 1, 10])
    with cols[0]:
        c = st.container(border=True, height=600)
        c.markdown(f"""<h4>{st.session_state['product_meta']['product_title']}</h4>""", unsafe_allow_html=True)
        c.markdown(f"""<h3>{st.session_state['product_meta']['product_price']}</h3>""", unsafe_allow_html=True)

        c.markdown(f"""<img src="{st.session_state['product_meta']['product_image']}" alt="drawing" width=400/>""", unsafe_allow_html=True)
        
    with cols[2]:
        # c = st.container(border=True, height=500, )            
        metrics = compute_aspect_metrics('review_rating')
        fig, ax = plt.subplots()
        centre_circle = plt.Circle(
                xy=(0, 0), 
                radius=0.60, 
                fc='white')
        ax.pie(
            metrics.values(), 
            labels=map_score_to_labels(metrics),
            radius=1,
            colors = ['#FF5D4B', '#FFA737','#FCD936', '#B4CE2D', '#3BA72E'],   # Green to red
            # wedgeprops = {"edgecolor" : "#191c21", 
            #         'linewidth': 1,
            #         'antialiased': True}
        )
        ax.add_artist(centre_circle)

        st.subheader('Overall review rating')
        st.pyplot(fig)

def display_aspect_level_pie_charts(opinion=False):
    # Tabs for each aspect
    for i, tab in enumerate(st.tabs([clean_dsiplay_names(x) for x in st.session_state["aspects"]])):
        with tab:
            # one col for pie chat, one for 'sample reviews'
            col1, col2 = st.columns([4,9])
            with col1:
                metrics = compute_aspect_metrics(st.session_state["aspects"][i], opinion)
                fig, ax = plt.subplots()
                centre_circle = plt.Circle(
                    xy=(0, 0), 
                    radius=0.60, 
                    fc='white')
                ax.pie(
                    metrics.values(), 
                    labels=map_score_to_labels(metrics),
                    radius=1,
                    # colors = ['#00946A', '#FF5741', '#FFDB2C', "#9a40f5"],     # Green, yellow, red and 'not mentioned'(purple)
                    colors = decide_colors(metrics),     # neg, neu, not, pos
                    # wedgeprops = {"edgecolor" : "#191c21", 
                    # 'linewidth': 1, 
                    # 'antialiased': True}
                )
                ax.add_artist(centre_circle)
                st.subheader(clean_dsiplay_names(st.session_state["aspects"][i]))
                st.pyplot(fig)
    
            with col2:                         
                cols = st.columns([1,1])
                with cols[0]:
                    st.write(f"{clean_dsiplay_names(st.session_state['aspects'][i])}: Positive Sentiment")
                    review_container1 = st.container(height=500)
                    # Positive reviews
                    display_sample_reviews(review_container1, st.session_state["aspects"][i], "POSITIVE", count=3, expand=st.session_state['expand'], opinion=True)
                with cols[1]:
                    st.write(f"{clean_dsiplay_names(st.session_state['aspects'][i])}: Negative Sentiment")
                    review_container2 = st.container(height=500)
                    # Negative reviews
                    display_sample_reviews(review_container2, st.session_state["aspects"][i], "NEGATIVE", count=3, expand=st.session_state['expand'], opinion=True)
             
# Main
product_name = st.selectbox("Choose product to analyze", options=sorted([p['product_title'] for p in st.session_state['all_product_meta']]))
st.divider()
product_info_mapper(product_name)    
st.session_state["df"] = pd.read_csv(f"data_files/{st.session_state['product_meta']['product_id']}.csv")
st.session_state["df"].dropna(inplace=True)
display_overview()
st.divider()

st.header("Aspect-wise rating")
display_aspect_level_pie_charts()