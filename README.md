# Korean → Bangla Vocabulary Tracker

প্রতিটা chapter এর word list upload করলেই আগের সব chapter এর সাথে compare করে শুধু নতুন/unique word বের করে Database এ save রাখে।

## Setup (একবার করতে হবে)

### ১. Supabase Database তৈরি
1. https://supabase.com এ free account খোলো, নতুন project তৈরি করো
2. Project এর মধ্যে **SQL Editor** এ যাও
3. এই repo এর `supabase_setup.sql` ফাইলের পুরো content কপি করে run করো — এতে `vocab_words` এবং `chapters_log` টেবিল তৈরি হবে
4. Project Settings → API থেকে **Project URL** ও **anon public key** কপি করে রাখো

### ২. Local এ চালাতে চাইলে
```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# secrets.toml ফাইলে নিজের SUPABASE_URL ও SUPABASE_KEY বসাও
streamlit run Home.py
```

### ৩. Streamlit Community Cloud এ Deploy
1. এই পুরো repo GitHub এ push করো (secrets.toml বাদে — .gitignore এ আছে)
2. https://share.streamlit.io এ গিয়ে GitHub repo connect করো, main file হিসেবে `Home.py` দাও
3. App এর **Settings → Secrets** এ গিয়ে নিচের মতো লিখো:
   ```
   SUPABASE_URL = "তোমার url"
   SUPABASE_KEY = "তোমার key"
   ```
4. Deploy করলেই app লাইভ হয়ে যাবে

## Pages
- **Home** — overview + quick stats
- **Upload Chapter** — নতুন chapter upload → column auto-detect → unique word বের করা → Excel/CSV download → Database তে save
- **Dashboard** — chapter-wise ও cumulative growth chart
- **Browse History** — আগের যেকোনো chapter এর word list দেখা/download

## Future এ নতুন app/page যোগ করা
`pages/` folder এ নতুন `.py` ফাইল যোগ করলেই সেটা sidebar এ নতুন page হিসেবে চলে আসবে। সব page একই `utils/db.py` দিয়ে Supabase এ connect হয়, তাই data সবসময় sync থাকবে।
