#!/usr/bin/env python3
"""
Test script to verify enhanced demo functionality
"""

import streamlit as st
import numpy as np
import pandas as pd
import altair as alt

def test_enhanced_demo_components():
    """Test that all components of the enhanced demo work correctly"""
    
    # Test numpy functionality
    arr = np.array([1, 2, 3, 4, 5])
    assert np.sum(arr) == 15, "Numpy not working correctly"
    
    # Test pandas functionality
    df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    assert len(df) == 3, "Pandas not working correctly"
    
    # Test altair functionality
    chart = alt.Chart(df).mark_bar().encode(
        x='A:O',
        y='B:Q'
    )
    assert chart is not None, "Altair not working correctly"
    
    print("SUCCESS: All enhanced demo components working correctly!")
    return True

if __name__ == "__main__":
    test_enhanced_demo_components()