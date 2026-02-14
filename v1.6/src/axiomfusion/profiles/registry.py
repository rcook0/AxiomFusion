from __future__ import annotations
from pathlib import Path
from typing import Dict, Optional
import json

from .schema import ExecutionProfile, load_profile_dict, ProfileError

DEFAULT_DIR = Path(__file__).resolve().parent / "data"

class ProfileNotFound(ProfileError): ...

def list_profiles(profiles_dir: Optional[str] = None) -> Dict[str, Path]:
    d = Path(profiles_dir) if profiles_dir else DEFAULT_DIR
    out: Dict[str, Path] = {}
    if not d.exists():
        return out
    for p in sorted(d.glob("*.json")):
        try:
            jd = json.loads(p.read_text(encoding="utf-8"))
            name = str(jd.get("name", p.stem))
            out[name] = p
        except Exception:
            continue
    return out

def load_profile(name: str, profiles_dir: Optional[str] = None) -> ExecutionProfile:
    d = Path(profiles_dir) if profiles_dir else DEFAULT_DIR
    # allow direct path
    p = Path(name)
    if p.exists():
        jd = json.loads(p.read_text(encoding="utf-8"))
        return load_profile_dict(jd)
    # search by name
    for cand in d.glob("*.json"):
        jd = json.loads(cand.read_text(encoding="utf-8"))
        if str(jd.get("name", cand.stem)).lower() == name.lower() or cand.stem.lower() == name.lower():
            return load_profile_dict(jd)
    raise ProfileNotFound(f"Profile not found: {name} (searched {d})")
