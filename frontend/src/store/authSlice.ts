import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import {
  fetchProfileRequest,
  loginRequest,
  logoutRequest,
  registerRequest,
  verifyEmailRequest,
  type Profile,
} from "../api/client";

export interface AuthState {
  user: Profile | null;
  loading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  loading: false,
  error: null,
};

export const login = createAsyncThunk<Profile, { email: string; password: string }>(
  "auth/login",
  async (data, { rejectWithValue }) => {
    try {
      await loginRequest(data);
      const profile = await fetchProfileRequest();
      return profile;
    } catch (err: any) {
      const message = err.response?.data?.detail || "Login failed";
      return rejectWithValue(message);
    }
  }
);

export const register = createAsyncThunk<
  void,
  { email: string; password: string; full_name: string }
>("auth/register", async (data, { rejectWithValue }) => {
  try {
    await registerRequest(data);
  } catch (err: any) {
    const message =
      err.response?.data?.detail || "Registration failed. Check your input.";
    return rejectWithValue(message);
  }
});

export const verifyEmail = createAsyncThunk<
  void,
  { email: string; code: string }
>("auth/verifyEmail", async (data, { rejectWithValue }) => {
  try {
    await verifyEmailRequest(data);
  } catch (err: any) {
    const message =
      err.response?.data?.detail || "Verification failed. Check the code.";
    return rejectWithValue(message);
  }
});

export const fetchProfile = createAsyncThunk<Profile>(
  "auth/fetchProfile",
  async (_, { rejectWithValue }) => {
    try {
      const profile = await fetchProfileRequest();
      return profile;
    } catch (err: any) {
      const message = err.response?.data?.detail || "Failed to load profile";
      return rejectWithValue(message);
    }
  }
);

export const logout = createAsyncThunk<void>(
  "auth/logout",
  async (_, { rejectWithValue }) => {
    try {
      await logoutRequest();
    } catch (err: any) {
      const message = err.response?.data?.detail || "Failed to logout";
      return rejectWithValue(message);
    }
  }
);

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload;
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        state.error = (action.payload as string) || "Login failed";
      })
      .addCase(register.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(register.fulfilled, (state) => {
        state.loading = false;
      })
      .addCase(register.rejected, (state, action) => {
        state.loading = false;
        state.error = (action.payload as string) || "Registration failed";
      })
      .addCase(verifyEmail.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(verifyEmail.fulfilled, (state) => {
        state.loading = false;
      })
      .addCase(verifyEmail.rejected, (state, action) => {
        state.loading = false;
        state.error = (action.payload as string) || "Verification failed";
      })
      .addCase(fetchProfile.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchProfile.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload;
      })
      .addCase(fetchProfile.rejected, (state) => {
        state.loading = false;
      })
      .addCase(logout.fulfilled, (state) => {
        state.user = null;
      });
  },
});

export const authReducer = authSlice.reducer;
