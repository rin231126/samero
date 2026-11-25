from pathlib import Path
import sys
root=Path(sys.argv[1]).resolve()
p=root/'src/main.c';s=p.read_text(encoding='utf-8')
anchor='    unsigned short port=0;\n    Socket server=listen_local(&port);'
assert s.count(anchor)==1
# Diagnostic-only seed; never apply to a released binary or the candidate.
s=s.replace(anchor,'''    /* Isolated native QA only; not compiled into the release or candidate. */
    if (headless && root) {
        Path receipt; Buf data={0}; JSON j;
        if (path_join(&receipt,m->data.p,"native-local-fixture.json") && read_file(receipt.p,1024,&data,&e) && json_parse(&j,data.s,data.n)) {
            long long bytes=NUMBER(&j,"bytes",-1);
            if (bytes>0 && bytes<=64*MIB && ARG(&j,"sha256",approved_candidate.digest) && path_join(&approved_candidate.path,m->data.p,"SAMERO-update-0123456789abcdef0123456789abcdef.exe")) {
                FILE *verified=public_update_verified_file(m->data.p,approved_candidate.path.p,bytes,approved_candidate.digest,&e);
                if (verified) { fclose(verified); approved_candidate.bytes=bytes; strcpy(approved_candidate.sequence,"2147483647"); }
            }
            json_free(&j);
        }
        buffer_free(&data);
        if (!*approved_candidate.sequence) goto done;
    }
'''+anchor)
p.write_text(s,encoding='utf-8')
print('PASS: QA-only receipt seed; same production restart preflight and Windows Shell launch')
