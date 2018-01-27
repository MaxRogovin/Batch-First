'''
Created on Jul 2, 2017

@author: SamRagusa
'''

import tensorflow as tf

import ann_creation_helper as ann_h


tf.logging.set_verbosity(tf.logging.INFO)



def main(unused_param):
    """
    Set up the data pipelines, create the computational graph, train the model, and evaluate the results.
    """
    SAVE_MODEL_DIR = "/srv/tmp/blahblah_6"
    TRAINING_FILENAMES = ["/srv/databases/chess_engine/full_3/shuffled_training_set.txt"]
    VALIDATION_FILENAMES = ["/srv/databases/chess_engine/full_5/scoring_validation_set.tfrecords"]
    TRAIN_OP_SUMMARIES = ["gradient_norm", "gradients"]
    NUM_OUTPUTS = 1
    DENSE_SHAPE = [2058,1024,512]
    OPTIMIZER = 'Adam'
    TRAINING_MIN_AFTER_DEQUEUE = 20000
    TRAINING_BATCH_SIZE = 512#1024
    EQUALITY_SCALAR_MULT = 1.01
    VALIDATION_BATCH_SIZE = 2000
    NUM_TRAINING_EPOCHS = 500
    LOG_ITERATION_INTERVAL =1000
    OLD_MOVE_SCALAR_MULT = 1.005
    LEARNING_RATE = .000001#.000002



    INCEPTION_MODULES = [
        [
            [[128,2],[256,2]],
            [[256,3]]],
        [
            [[256,1]],
            [[64,1], [128,1,6]],
            [[64,1], [128,6,1]]]]  #Output of 10752 neurons




    BATCHES_IN_TRAINING_EPOCH = 758545383  // TRAINING_BATCH_SIZE
    #reduce(
        # lambda x, y: x + y,
        # [ann_h.line_counter(filename) for filename in TRAINING_FILENAMES]) // (TRAINING_BATCH_SIZE * 10)
    BATCHES_IN_VALIDATION_EPOCH = 1000000// VALIDATION_BATCH_SIZE
    #84289074 // VALIDATION_BATCH_SIZE
    #ann_h.line_counter(VALIDATION_FILENAMES[0]) // VALIDATION_BATCH_SIZE


    learning_decay_function = lambda gs  : tf.train.exponential_decay(LEARNING_RATE,
                                                                      global_step=gs,
                                                                      decay_steps=BATCHES_IN_TRAINING_EPOCH//15,
                                                                      decay_rate=0.92,
                                                                      staircase=True)

    print(BATCHES_IN_TRAINING_EPOCH)
    print(BATCHES_IN_VALIDATION_EPOCH)


    # Create the Estimator
    classifier = tf.estimator.Estimator(
        model_fn=ann_h.cnn_model_fn,
        model_dir=SAVE_MODEL_DIR,
        config=tf.estimator.RunConfig().replace(
            save_checkpoints_steps=LOG_ITERATION_INTERVAL,
            save_summary_steps=LOG_ITERATION_INTERVAL),
            # session_config=tf.ConfigProto(log_device_placement=True)),
        params={
            "dense_shape": DENSE_SHAPE,
            "optimizer": OPTIMIZER,
            "num_outputs": NUM_OUTPUTS,
            "log_interval": LOG_ITERATION_INTERVAL,
            "model_dir": SAVE_MODEL_DIR,
            "inception_modules" : INCEPTION_MODULES,
            "learning_rate": LEARNING_RATE,
            "train_summaries": TRAIN_OP_SUMMARIES,
            "learning_decay_function" : learning_decay_function,
            "inc_old_move_scalar" : OLD_MOVE_SCALAR_MULT,
            "equality_scalar": EQUALITY_SCALAR_MULT})

    validation_hook = ann_h.ValidationRunHook(
        step_increment=BATCHES_IN_TRAINING_EPOCH//(5*300),
        estimator=classifier,
        input_fn_creator=lambda: ann_h.one_hot_create_tf_records_input_data_fn(VALIDATION_FILENAMES,VALIDATION_BATCH_SIZE),
        temp_num_steps_in_epoch=500)#BATCHES_IN_VALIDATION_EPOCH)

    classifier.train(
        input_fn=lambda: ann_h.input_data_fn(
            TRAINING_FILENAMES,
            TRAINING_BATCH_SIZE,
            NUM_TRAINING_EPOCHS,
            TRAINING_MIN_AFTER_DEQUEUE,
            True),
        hooks=[validation_hook],
        # max_steps=1,
    )


    # Export the model for serving
    classifier.export_savedmodel(
        SAVE_MODEL_DIR,
        serving_input_receiver_fn=ann_h.new_serving_input_reciever_fn,
        as_text=True)




if __name__ == "__main__":
    tf.app.run()