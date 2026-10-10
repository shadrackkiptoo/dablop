-- Allow the screenshot upload path to work with a public Supabase bucket.
-- Run this migration after 000_all.sql on an existing project.

drop policy if exists screenshots_deny_client on public.screenshots;
drop policy if exists screenshots_public_read on public.screenshots;
drop policy if exists screenshots_public_insert on public.screenshots;

create policy screenshots_public_read on public.screenshots
  for select to anon, authenticated using (true);

create policy screenshots_public_insert on public.screenshots
  for insert to anon, authenticated with check (true);

insert into storage.buckets (id, name, public)
values ('screenshots', 'screenshots', true)
on conflict (id) do update set public = true;

drop policy if exists screenshots_storage_public_insert on storage.objects;
create policy screenshots_storage_public_insert on storage.objects
  for insert to anon, authenticated
  with check (
    bucket_id = 'screenshots'
    and name ~ '^[^/]+/[0-9]+[.]png$'
  );

drop policy if exists screenshots_storage_public_read on storage.objects;
create policy screenshots_storage_public_read on storage.objects
  for select to anon, authenticated
  using (bucket_id = 'screenshots');