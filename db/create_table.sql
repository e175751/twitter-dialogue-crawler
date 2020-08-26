create table status(
    id bigint NOT NULL,
    text text NOT NULL,
    in_reply_to_status_id bigint default 0,
    user_id bigint NOT NULL,
    is_quote_status integer NOT NULL,
    created_at integer NOT NULL,
    CONSTRAINT status_id PRIMARY KEY (id)
);

create table conversation(
    id serial,
    ids JSON NOT NULL,
    CONSTRAINT converstaion_id PRIMARY KEY (id)
);