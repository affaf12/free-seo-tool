import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import time
import json

st.set_page_config(page_title="Pro+ SEO Analyzer", layout="wide")
st.title("🚀 Pro+ SEO Analyzer")
st.write("Advanced On-Page, Technical, Off-Page, Semantic SEO Analysis, and SERP Estimation with actionable recommendations!")

# ---------- Helper Functions ----------
def get_html(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Pro+SEO-Analyzer)"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        st.error(f"Failed to fetch website HTML: {e}")
        return None

def extract_meta(soup):
    title = soup.title.string.strip() if soup.title else ""
    desc = soup.find("meta", attrs={"name": "description"})
    desc = desc["content"] if desc and "content" in desc.attrs else ""
    canonical = soup.find("link", rel="canonical")
    canonical = canonical["href"] if canonical else ""
    viewport = soup.find("meta", attrs={"name": "viewport"})
    viewport = viewport["content"] if viewport and "content" in viewport.attrs else ""
    return {"title": title, "description": desc, "canonical": canonical, "viewport": viewport}

def get_headings(soup):
    headings = {}
    for tag in ["h1", "h2", "h3"]:
        headings[tag] = [h.get_text(strip=True) for h in soup.find_all(tag)]
    return headings

def get_word_stats(soup):
    text = soup.get_text(separator=" ", strip=True)
    words = re.findall(r"\b\w+\b", text)
    total = len(words)
    top_words = {}
    for w in words:
        w = w.lower()
        top_words[w] = top_words.get(w, 0) + 1
    top = sorted(top_words.items(), key=lambda x: x[1], reverse=True)[:20]
    return total, top, text

def robots_and_sitemap(url):
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    try:
        robots = requests.get(urljoin(base, "/robots.txt"), timeout=10).text[:1000]
    except:
        robots = "robots.txt not available"
    try:
        sitemap = requests.get(urljoin(base, "/sitemap.xml"), timeout=10).text[:1000]
    except:
        sitemap = "sitemap.xml not available"
    return robots, sitemap

def pagespeed_api(url):
    api_key = "YOUR_API_KEY_HERE"
    api = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&key={api_key}"
    try:
        resp = requests.get(api, timeout=15)
        data = resp.json()
        if "lighthouseResult" in data and "categories" in data["lighthouseResult"]:
            score = data["lighthouseResult"]["categories"]["performance"]["score"] * 100
            return score
        else:
            return None
    except:
        return None

def simple_speed_test(url):
    start = time.time()
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return round(time.time() - start, 2)
    except:
        return None

# ---------- Scoring Functions ----------
def calculate_onpage_score(meta, headings, total_words):
    score = 0
    suggestions = []
    if 10 <= len(meta["title"]) <= 60: score += 20
    else: suggestions.append("Title length should be 10-60 characters")
    if 50 <= len(meta["description"]) <= 160: score += 20
    else: suggestions.append("Meta description should be 50-160 characters")
    if len(headings["h1"]) >= 1: score += 20
    else: suggestions.append("Add at least one H1 heading")
    if total_words >= 300: score += 20
    else: suggestions.append("Add more content (min 300 words)")
    if meta["canonical"]: score += 20
    else: suggestions.append("Add a canonical tag")
    return score, suggestions

def calculate_technical_score(robots, sitemap, viewport, soup):
    score = 0
    suggestions = []
    if "not available" not in robots.lower(): score += 30
    else: suggestions.append("Add robots.txt")
    if "not available" not in sitemap.lower(): score += 30
    else: suggestions.append("Add sitemap.xml")
    if viewport: score += 20
    else: suggestions.append("Add viewport meta for mobile-friendliness")
    # Structured data check
    schema_found = bool(soup.find_all("script", type="application/ld+json"))
    if schema_found: score += 20
    else: suggestions.append("Add structured data / schema (JSON-LD recommended)")
    return score, suggestions

def calculate_offpage_score():
    score = 50
    suggestions = ["Check backlinks and domain authority"]
    return score, suggestions

def calculate_semantic_score(text, main_keyword="seo"):
    keyword_count = text.lower().count(main_keyword.lower())
    total_words = len(text.split())
    density = (keyword_count / total_words) * 100 if total_words else 0
    score = min(100, density * 2)
    suggestions = []
    if density < 1: suggestions.append(f"Use keyword '{main_keyword}' more frequently (density: {density:.2f}%)")
    elif density > 5: suggestions.append(f"Keyword '{main_keyword}' density too high (density: {density:.2f}%)")
    return int(score), suggestions

# ---------- SERP Rank Estimator ----------
def estimate_serp_rank(overall_score):
    if overall_score >= 90: return "Estimated SERP Rank: 1-3"
    elif overall_score >= 80: return "Estimated SERP Rank: 4-10"
    elif overall_score >= 70: return "Estimated SERP Rank: 11-20"
    elif overall_score >= 60: return "Estimated SERP Rank: 21-50"
    else: return "Estimated SERP Rank: 50+"

# ---------- UI ----------
url = st.text_input("Enter URL", "https://example.com")
main_keyword = st.text_input("Main SEO Keyword (for semantic analysis)", "seo")

if st.button("Analyze SEO"):
    html = get_html(url)
    if not html:
        st.error("Failed to fetch website.")
    else:
        soup = BeautifulSoup(html, "html.parser")
        meta = extract_meta(soup)
        headings = get_headings(soup)
        total_words, top_words, full_text = get_word_stats(soup)
        robots, sitemap = robots_and_sitemap(url)
        speed_score = pagespeed_api(url) or simple_speed_test(url)

        # ---------- Calculate Scores ----------
        onpage_score, onpage_sugg = calculate_onpage_score(meta, headings, total_words)
        technical_score, technical_sugg = calculate_technical_score(robots, sitemap, meta["viewport"], soup)
        offpage_score, offpage_sugg = calculate_offpage_score()
        semantic_score, semantic_sugg = calculate_semantic_score(full_text, main_keyword)
        overall_score = round((onpage_score + technical_score + offpage_score + semantic_score)/4)
        serp_estimate = estimate_serp_rank(overall_score)

        # ---------- Display Scores ----------
        st.header("📊 SEO Scores")
        st.subheader("On-Page SEO"); st.progress(onpage_score); st.write(f"{onpage_score}/100"); [st.write("•", s) for s in onpage_sugg]
        st.subheader("Technical SEO"); st.progress(technical_score); st.write(f"{technical_score}/100"); [st.write("•", s) for s in technical_sugg]
        st.subheader("Off-Page SEO"); st.progress(offpage_score); st.write(f"{offpage_score}/100"); [st.write("•", s) for s in offpage_sugg]
        st.subheader("Semantic / Keyword SEO"); st.progress(semantic_score); st.write(f"{semantic_score}/100"); [st.write("•", s) for s in semantic_sugg]
        st.subheader("Overall SEO Score"); st.progress(overall_score); st.write(f"Overall Score: {overall_score}/100")
        st.subheader("📈 Google SERP Rank Estimator"); st.success(serp_estimate)

        # ---------- Detailed On-Page ----------
        st.header("🔍 Detailed On-Page SEO")
        st.write("**Title:**", meta["title"])
        st.write("**Description:**", meta["description"])
        st.write("**Canonical:**", meta["canonical"] or "No canonical tag found")
        st.write("**Word Count:**", total_words)
        st.write("**Top Words:**", top_words)
        st.write("**Headings:**"); [st.write(f"{tag.upper()} ({len(vals)}) → {vals[:5]}") for tag, vals in headings.items()]

        # ---------- Detailed Technical ----------
        st.header("⚙️ Detailed Technical SEO")
        st.write("**robots.txt:**"); st.code(robots)
        st.write("**sitemap.xml:**"); st.code(sitemap)
        st.write("**Viewport Meta:**", meta["viewport"] or "Not found")
        if speed_score: st.write(f"⏱️ Page Load Time / Speed Score: {speed_score}")
        else: st.warning("Could not determine page speed")
        st.write("**Structured Data (JSON-LD):**")
        json_ld_scripts = soup.find_all("script", type="application/ld+json")
        if json_ld_scripts:
            for s in json_ld_scripts: st.code(json.loads(s.string))
        else:
            st.write("No structured data found")
