#!/usr/bin/env python3
# encoding: utf-8

def get_stored_data(wf, key):
    """Get data from workflow storage"""
    try:
        return wf.stored_data(key)
    except Exception:
        return None

def save_stored_data(wf, key, data):
    """Save data to workflow storage"""
    try:
        wf.store_data(key, data)
        return True
    except Exception:
        return False 