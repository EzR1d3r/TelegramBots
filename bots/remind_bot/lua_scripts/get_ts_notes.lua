--EVAL script 0 s_timestamp timestamp s_note s_uid

local ts_key = ARGV[1]..':'..ARGV[2]
local uids = redis.call('smembers', ts_key)
local notes = {}
for i = 1, #uids do
    local note_key = ARGV[3]..':'..uids[i]
    local note = redis.call( 'hgetall', note_key )
    note[#note + 1], note[#note + 2] = ARGV[4], uids[i]
    notes[i] = note
end
return notes