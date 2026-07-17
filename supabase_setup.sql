-- Supabase SQL editor এ এই পুরো script একবার run করলেই টেবিল তৈরি হয়ে যাবে।

create table if not exists vocab_words (
    id bigint generated always as identity primary key,
    korean_word text not null,
    bangla_meaning text,
    chapter_number int not null,
    date_added timestamptz default now()
);

create table if not exists chapters_log (
    chapter_number int primary key,
    total_words_in_file int,
    unique_new_words int,
    upload_date timestamptz default now()
);

-- দ্রুত lookup এর জন্য index (একই Korean word বারবার আছে কিনা চেক করতে কাজে লাগবে)
create index if not exists idx_vocab_korean_word on vocab_words (korean_word);
