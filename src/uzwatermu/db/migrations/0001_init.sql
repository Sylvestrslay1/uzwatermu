create table schema_version (
    version integer primary key,
    applied_at text not null default current_timestamp
);

create table abonents (
    account text primary key,
    fio text not null default '',
    phone text not null default '',
    address text not null default '',
    area text not null default '',
    inspector_fio text not null default '',
    inspector_phone text not null default '',
    debit text not null default '',
    credit text not null default '',
    imported_at text not null default current_timestamp
);

create table users (
    telegram_id integer primary key,
    language text not null default 'uz' check (language in ('uz', 'uz_cyrl', 'ru')),
    role text not null default 'user' check (role in ('user', 'operator', 'admin')),
    created_at text not null default current_timestamp
);

create table user_accounts (
    telegram_id integer not null references users(telegram_id) on delete cascade,
    account text not null references abonents(account),
    status text not null default 'pending' check (status in ('pending', 'approved', 'rejected')),
    decided_by integer,
    created_at text not null default current_timestamp,
    decided_at text,
    primary key (telegram_id, account)
);

create table submissions (
    id integer primary key autoincrement,
    telegram_id integer not null references users(telegram_id),
    account text not null references abonents(account),
    photo_file_ids text not null,
    photo_sha256 text not null,
    status text not null default 'received'
        check (status in ('received', 'approved', 'rejected')),
    created_at text not null default current_timestamp
);
create index idx_submissions_account on submissions(account, created_at);
create index idx_submissions_sha on submissions(photo_sha256);

create table audit_log (
    id integer primary key autoincrement,
    actor_id integer,
    action text not null,
    details text not null default '',
    created_at text not null default current_timestamp
);

create table conversation_state (
    telegram_id integer primary key,
    state text not null,
    data text not null default '{}',
    updated_at text not null default current_timestamp
);
