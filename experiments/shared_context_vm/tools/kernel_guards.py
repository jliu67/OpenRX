"""Exact selected accepted kernel guard functions; no observer main/import/lock."""
def kernel_resources(unit, cgroup_root=Path("/sys/fs/cgroup")):
    """Read this service and every visible ancestor; never use manager properties."""
    group = own_cgroup(unit)
    if group is None:
        # Direct nonproduction worker tests have no named unit. The production
        # private CLI rejects that condition before entering worker().
        return None
    relative = group[0]
    if not relative.startswith("/") or ".." in Path(relative).parts:
        raise ValueError("Unsafe named service cgroup path")
    base = Path(cgroup_root).resolve()
    directory = base / relative.lstrip("/")
    records = []
    names = ("cpu.max", "memory.max", "memory.high", "memory.swap.max", "pids.max",
             "cgroup.controllers", "cgroup.subtree_control", "cpuset.cpus.effective")
    while True:
        files = {}
        for name in names:
            try:
                files[name] = (directory / name).read_text().strip()
            except FileNotFoundError:
                files[name] = None
        records.append({"path": str(directory), "is_root": directory == base, "files": files})
        if directory == base:
            break
        directory = directory.parent
    return {"at": now(), "service_cgroup": relative, "groups": records,
            "worker_allowed_cpus": sorted(os.sched_getaffinity(0))}


def kernel_resource_errors(observed, profile):
    errors = []
    if not observed["groups"]:
        return ["No named service kernel cgroup was observed"]
    memory = profile["kernel_memory_max_bytes"]
    if memory <= 0:
        errors.append("Requested memory is smaller than one kernel page")
    if len(observed["worker_allowed_cpus"]) < 6:
        errors.append("Worker affinity exposes fewer than six CPUs")
    for index, group in enumerate(observed["groups"]):
        values = group["files"]
        path = group["path"]
        cpu = values["cpu.max"]
        if cpu is not None:
            match = re.fullmatch(r"(max|[1-9]\d*) ([1-9]\d*)", cpu)
            if match is None or (index == 0 and (match[1] == "max" or int(match[1]) != 6 * int(match[2]))) or (match[1] != "max" and int(match[1]) < 6 * int(match[2])):
                errors.append(f"Missing, invalid or tighter CPU quota: {path}")
        elif not group["is_root"]:
            errors.append(f"Missing CPU controller limit: {path}")
        for name, expected in (("memory.max", memory), ("memory.high", memory),
                               ("memory.swap.max", 2 * GIB), ("pids.max", 256)):
            value = values[name]
            if value is None:
                if not group["is_root"]:
                    errors.append(f"Missing {name} controller limit: {path}")
                continue
            if not re.fullmatch(r"max|\d+", value):
                errors.append(f"Invalid {name}: {path}")
                continue
            exact = index == 0 and name != "memory.high"
            if (exact and value != str(expected)) or (value != "max" and int(value) < expected):
                errors.append(f"Missing, invalid or tighter {name}: {path}")
        cpus = values["cpuset.cpus.effective"]
        if cpus is not None:
            allowed = set()
            for item in cpus.split(","):
                match = re.fullmatch(r"(\d+)(?:-(\d+))?", item)
                if match is None or int(match[1]) > int(match[2] or match[1]) or int(match[2] or match[1]) > 65535:
                    errors.append(f"Invalid effective CPU set: {path}")
                    break
                allowed.update(range(int(match[1]), int(match[2] or match[1]) + 1))
            if len(allowed & set(observed["worker_allowed_cpus"])) < 6:
                errors.append(f"Effective CPU availability is below six: {path}")
    return errors


def own_cgroup(unit):
    """Resolve only this named systemd service, never a shared caller cgroup."""
    for line in Path("/proc/self/cgroup").read_text().splitlines():
        if line.startswith("0::"):
            relative = line[3:]
            if relative.endswith("/" + unit):
                return relative, Path("/sys/fs/cgroup") / relative.lstrip("/")
    return None


def effective(observed):
    quota=None;eligible=set(observed['worker_allowed_cpus']);hard={k:[]for k in ('memory.max','memory.swap.max','pids.max')}
    for row in observed['groups']:
        f=row['files'];cpu=f['cpu.max']
        if cpu is not None:
            q,p=cpu.split()
            if q!='max':
                pair=(int(q),int(p))
                if quota is None or pair[0]*quota[1]<quota[0]*pair[1]:quota=pair
        for k in hard:
            if f[k] is not None and f[k]!='max':hard[k].append(int(f[k]))
        if f['cpuset.cpus.effective']is not None:
            cpus=set()
            for part in f['cpuset.cpus.effective'].split(','):
                a,sep,b=part.partition('-');cpus.update(range(int(a),int(b or a)+1))
            eligible &= cpus
    return {'minimum_hierarchical_cpu_quota':list(quota)if quota else None,
        'eligible_cpus':sorted(eligible),'effective_memory_max_bytes':min(hard['memory.max']),
        'effective_swap_max_bytes':min(hard['memory.swap.max']),'effective_tasks_max':min(hard['pids.max']),
        'scope':'Kernel caps/eligible CPUs, not reserved CPU time, swap reservation, sustained speed or PPA.'}

