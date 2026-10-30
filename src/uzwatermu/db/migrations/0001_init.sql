-- Abonentlarning shaxsiy ma'lumotlari (F.I.O, telefon, manzil, balans) bu bazada saqlanmaydi:
-- ular faqat RAM'da, import papkasidagi Excel'dan yuklanadi. Bu yerda faqat bog'lanishlar va holatlar.

create table schema_version (
    version integer primary key,
    applied_at text not null default current_timestamp
);

create table users (
    telegram_id integer primary key,
    language text check (language in ('uz', 'uz_cyrl', 'ru')),
    role text not null default 'user'
        check (role in ('user', 'operator', 'inspector', 'admin')),
    -- Favqulodda bekor qilingan akkaunt: .env dagi asosiy admin bo'lsa ham qayta tiklanmaydi.
    revoked_at text,
    created_at text not null default current_timestamp,
    updated_at text not null default current_timestamp
);

create table account_links (
    telegram_id integer not null references users(telegram_id) on delete cascade,
    account text not null,
    status text not null check (status in ('pending', 'approved', 'rejected', 'unlinked')),
    method text check (method in ('auto', 'operator')),
    decided_by integer,
    reject_reason text,
    created_at text not null default current_timestamp,
    decided_at text,
    primary key (telegram_id, account)
);
create index idx_account_links_account on account_links(account, status);

create table settings (
    key text primary key,
    value text not null,
    updated_by integer,
    updated_at text not null default current_timestamp
);

create table audit_log (
    id integer primary key autoincrement,
    actor_id integer,
    action text not null,
    details text not null default '',
    created_at text not null default current_timestamp
);
create index idx_audit_log_created on audit_log(created_at);
create index idx_audit_log_actor on audit_log(actor_id, created_at);
