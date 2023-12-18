create table if not exists all_cards (
    id text,
    name text primary key,
    type text,
    descript text,
    race text,
    archetype text,
    atk int,
    def int,
    level int,
    attribute text,
    scale int,
    linkval int,
    tcg_date text,
    ocg_date text);

create table if not exists sets (
    id text,
    name text,
    set_code text,
    set_id text,
    set_rarity text,
    set_rarity_code text,
    constraint sets_FK foreign key (name) references all_cards(name));

create table if not exists banlist (
    id text,
    name text,
    tcg text,
    ocg text,
    goat text,
    constraint banlist_FK foreign key (name) references all_cards(name));

create table if not exists formats (
    id text,
    name text,
    format text,
    constraint format_FK foreign key (name) references all_cards(name));

create table if not exists set_list (
    set_code text primary key,
    set_name text,
    size int,
    release text,
    subset text);

create table if not exists set_cards (
   id text,
   name text,
   set_code text,
   set_id text,
   set_rarity text,
   owned int,
   constraint set_cards_FK foreign key (name) references all_cards(name),
   constraint set_cards_FK_1 foreign key (set_code) references set_list(set_code));

create table if not exists db_version (version text, date text);

create table if not exists all_sets (
    name text,
    code text,
    size int,
    date text);

create virtual table if not exists tri using fts5(name, archetype, tokenize='trigram');

create virtual table if not exists sets_tri using fts5(name, code, tokenize='trigram');