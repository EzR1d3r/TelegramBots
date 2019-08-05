--EVAL script 1 usr_notes_key s_note s_uid

local usr_notes_uids = redis.call( 'smembers', KEYS[1] )
local notes = {}
for i = 1, #usr_notes_uids do
    local note_key = ARGV[1]..':'..usr_notes_uids[i]
    local note = redis.call( 'hgetall', note_key )
    if #note == 0 then
        redis.call('srem', KEYS[1], usr_notes_uids[i])
    else
        note[#note + 1], note[#note + 2] = ARGV[2], usr_notes_uids[i]
        notes[i] = note
    end
end
return notes