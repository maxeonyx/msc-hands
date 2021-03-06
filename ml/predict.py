import tensorflow as tf

def create_predict_fn(cfg, dist_fn, get_angle_fn, model):
    """
    Create a predict function that does autoregressive sampling.
    """

    @tf.function
    def predict(x, n_frames):
        batch_size = x["angles"].shape[0]

        params = model(x, training=False)
        dist = dist_fn(params)
        angles = get_angle_fn(dist)

        frame_idxs = x["frame_idxs"]
        hand_idxs = x["hand_idxs"]
        dof_idxs = x["dof_idxs"]
        
        if frame_idxs.shape[1] == 0:
            start_frame = tf.zeros([batch_size, 1], dtype=tf.int32)
        else:
            start_frame = frame_idxs[:, -1:] + 1

        # use chunk size - 1 so that we stay in-distribution
        n_chunk_toks = (cfg.chunk_size - 1) * cfg.n_hands * cfg.n_dof

        # tile a constant value to the batch dimension and len=1 seq dim
        def tile_batch_seq(x):
            return tf.tile(x[None, None], [batch_size, 1])

        # produce F*H*D - 1 predictions
        # the minus one is because we don't need to predict the last frame
        # eg. if i=99, then we don't need to predict frame 100 (it's out of bounds)
        def cond(i, angles, frame_idxs, hand_idxs, dof_idxs):
            return tf.less(i, n_frames*cfg.n_hands*cfg.n_dof-1)
        
        def body(i, angles, frame_idxs, hand_idxs, dof_idxs):

            i_frame_offset = i // (cfg.n_hands * cfg.n_dof)
            i_frame = start_frame + i_frame_offset[None, None]
            i_hand = (i // cfg.n_dof) % cfg.n_hands
            i_dof = i % cfg.n_dof
            
            frame_idxs = tf.concat([frame_idxs, i_frame], axis=-1)

            hand_idxs = tf.concat([hand_idxs, tile_batch_seq(i_hand)], axis=-1)
            dof_idxs  = tf.concat([dof_idxs,  tile_batch_seq(i_dof)],  axis=-1)
            
            # use a fixed length context window to predict the next frame
            start_idx = tf.math.maximum(0, tf.shape(frame_idxs)[1]-n_chunk_toks)
            inputs = {
                "angles": angles[:, start_idx:],
                "frame_idxs": frame_idxs[:, start_idx:],
                "hand_idxs": hand_idxs[:, start_idx:],
                "dof_idxs": dof_idxs[:, start_idx:],
            }
            params = model(inputs, training=False) # model outputs a sequence, but we only need the new token
            dist = dist_fn(params[:, -1:, :])
            new_angles = get_angle_fn(dist)

            angles = tf.concat([angles, new_angles], axis=1)
            
            return i+1, angles, frame_idxs, hand_idxs, dof_idxs
        
        _i, angles, _frame_idxs, _hand_idxs, _dof_idxs = tf.while_loop(
            cond,
            body,
            loop_vars=[
                tf.constant(0),
                angles,
                frame_idxs,
                hand_idxs,
                dof_idxs,
            ],
            shape_invariants=[
                tf.TensorShape([]),
                tf.TensorShape([batch_size, None]),
                tf.TensorShape([batch_size, None]),
                tf.TensorShape([batch_size, None]),
                tf.TensorShape([batch_size, None]),
            ],
        )
        
        return angles
    
    return predict
